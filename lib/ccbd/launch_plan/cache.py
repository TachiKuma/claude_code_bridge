"""Launch Plan 项目级缓存与局部失效。

在 T01 的 LaunchPlan 指纹基础上，引入项目级缓存，按输入指纹失效。
缓存命中时跳过对应的 provider home / settings 写入和启动动作。
某个 agent 的缓存失效时只重建该 agent，不做全量重建。"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from storage.atomic import atomic_write_text, ensure_durable_directory

from .models import LaunchPlan


CACHE_DIR_NAME = 'launch-plan-cache'
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CachedLaunchPlan:
    """单个缓存条目，包含指纹比对所需的完整信息。"""

    agent_name: str
    fingerprint: str
    project_id: str
    plan_json: str
    receipt_hash: str
    created_at: str

    def to_record(self) -> dict[str, object]:
        return {
            'schema_version': SCHEMA_VERSION,
            'record_type': 'launch_plan_cache',
            'agent_name': self.agent_name,
            'fingerprint': self.fingerprint,
            'project_id': self.project_id,
            'plan_json': self.plan_json,
            'receipt_hash': self.receipt_hash,
            'created_at': self.created_at,
        }

    @classmethod
    def from_record(cls, record: dict[str, object]) -> CachedLaunchPlan:
        if record.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('unsupported cache schema version')
        if record.get('record_type') != 'launch_plan_cache':
            raise ValueError('invalid cache record type')
        agent_name = _required_text(record.get('agent_name'), field='agent_name')
        fingerprint = _required_text(record.get('fingerprint'), field='fingerprint')
        project_id = _required_text(record.get('project_id'), field='project_id')
        plan_json = _required_text(record.get('plan_json'), field='plan_json')
        receipt_hash = _required_text(record.get('receipt_hash'), field='receipt_hash')
        created_at = _required_text(record.get('created_at'), field='created_at')
        return cls(
            agent_name=agent_name,
            fingerprint=fingerprint,
            project_id=project_id,
            plan_json=plan_json,
            receipt_hash=receipt_hash,
            created_at=created_at,
        )


@dataclass
class LaunchPlanCacheMetrics:
    """缓存操作的度量收集。"""

    hit_count: int = 0
    write_count: int = 0
    write_skip_count: int = 0
    invalidation_count: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            'cache_hit_count': self.hit_count,
            'cache_write_count': self.write_count,
            'cache_write_skip_count': self.write_skip_count,
            'cache_invalidation_count': self.invalidation_count,
        }


class LaunchPlanCache:
    """项目级 Launch Plan 缓存，按输入指纹失效。

    缓存存放在项目根目录的 ``.ccb/launch-plan-cache/`` 下。
    每个 agent 一个独立的缓存文件。
    """

    def __init__(
        self,
        project_root: Path,
        project_id: str,
        *,
        clock=None,
    ) -> None:
        self._project_root = Path(project_root).expanduser().resolve()
        self._project_id = project_id
        self._cache_dir = self._project_root / '.ccb' / CACHE_DIR_NAME
        self._clock = clock or _utc_now_iso
        self._metrics = LaunchPlanCacheMetrics()

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @property
    def metrics(self) -> LaunchPlanCacheMetrics:
        return self._metrics

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def cache_key(self, agent_name: str, fingerprint: str) -> str:
        """基于 agent_name + fingerprint + project_id 的稳定复合缓存 key。

        不包含 timestamp、seq 等运行时状态。
        """
        raw = f'{self._project_id}:{agent_name}:{fingerprint}'
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def lookup(self, agent_name: str, fingerprint: str) -> CachedLaunchPlan | None:
        """按 agent_name + fingerprint 查询缓存。

        返回 CachedLaunchPlan（缓存命中）或 None（缓存不存在或指纹不匹配）。
        """
        path = self._agent_cache_path(agent_name)
        if not path.is_file():
            return None
        try:
            record = json.loads(path.read_text(encoding='utf-8'))
            cached = CachedLaunchPlan.from_record(record)
        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            return None

        expected_key = self.cache_key(agent_name, fingerprint)
        if cached.fingerprint != fingerprint:
            return None
        if cached.project_id != self._project_id:
            return None
        if self.cache_key(agent_name, cached.fingerprint) != expected_key:
            return None
        self._metrics.hit_count += 1
        return cached

    def write(
        self,
        agent_name: str,
        fingerprint: str,
        launch_plan: LaunchPlan | None,
        *,
        receipt_hash: str | None = None,
    ) -> bool:
        """原子写入一个 agent 的缓存条目。

        返回 True 表示写入（新写或内容变化），False 表示跳过（内容相同）。
        """
        plan_json = (
            _launch_plan_to_json(launch_plan)
            if launch_plan is not None
            else 'null'
        )
        effective_receipt_hash = str(receipt_hash or '').strip() or _compute_receipt(plan_json)

        cached = CachedLaunchPlan(
            agent_name=agent_name,
            fingerprint=fingerprint,
            project_id=self._project_id,
            plan_json=plan_json,
            receipt_hash=effective_receipt_hash,
            created_at=self._clock(),
        )
        text = json.dumps(cached.to_record(), ensure_ascii=False, indent=2) + '\n'

        path = self._agent_cache_path(agent_name)
        ensure_durable_directory(path.parent)

        # 内容无变化时跳过写入
        try:
            if path.read_text(encoding='utf-8') == text:
                self._metrics.write_skip_count += 1
                return False
        except FileNotFoundError:
            pass
        except (OSError, UnicodeError):
            pass

        atomic_write_text(path, text)
        self._metrics.write_count += 1
        return True

    def invalidate(self, agent_name: str) -> bool:
        """删除指定 agent 的缓存条目（局部失效）。

        返回 True 表示有缓存被删除，False 表示该 agent 无缓存。
        """
        path = self._agent_cache_path(agent_name)
        if not path.is_file():
            return False
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        except OSError:
            path.unlink(missing_ok=True)
        self._metrics.invalidation_count += 1
        return True

    def invalidate_all(self) -> int:
        """清除所有 launch plan 缓存。返回被删除的条目数。"""
        if not self._cache_dir.is_dir():
            return 0
        count = 0
        for child in list(self._cache_dir.iterdir()):
            if child.is_file() and child.suffix == '.json':
                try:
                    child.unlink()
                    count += 1
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
        self._metrics.invalidation_count += count
        return count

    def is_cached(self, agent_name: str, fingerprint: str) -> bool:
        """检查指定 agent 是否命中缓存（基于指纹比对）。"""
        return self.lookup(agent_name, fingerprint) is not None

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _agent_cache_path(self, agent_name: str) -> Path:
        """返回单个 agent 的缓存文件路径。"""
        safe_name = agent_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        return self._cache_dir / f'{safe_name}.json'


def _required_text(value: object, *, field: str) -> str:
    text = str(value or '').strip()
    if not text:
        raise ValueError(f'{field} is required')
    return text


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _launch_plan_to_json(plan: LaunchPlan) -> str:
    return json.dumps(
        {
            'agent_name': plan.agent_name,
            'provider': plan.provider,
            'provider_entry': plan.provider_entry,
            'model': plan.model,
            'thinking': plan.thinking,
            'startup_args': list(plan.startup_args),
            'workdir': plan.workdir,
            'env': [list(item) for item in plan.env],
            'session_anchor': plan.session_anchor,
            'runtime_binding_expected': plan.runtime_binding_expected,
            'fingerprint': plan.fingerprint,
        },
        ensure_ascii=False,
        default=str,
    )


def _compute_receipt(plan_json: str) -> str:
    """计算 plan_json 的 receipt hash，用于检测内容变化。"""
    return hashlib.sha256(plan_json.encode('utf-8')).hexdigest()
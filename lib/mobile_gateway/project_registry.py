from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class MobileGatewayProject:
    project_id: str
    project_root: Path
    ccbd_client_factory: Callable[[], object]
    display_name: str | None = None

    def __post_init__(self) -> None:
        project_id = str(self.project_id or '').strip()
        if not project_id:
            raise ValueError('project_id cannot be empty')
        object.__setattr__(self, 'project_id', project_id)
        object.__setattr__(self, 'project_root', Path(self.project_root))
        display_name = str(self.display_name or '').strip() or None
        object.__setattr__(self, 'display_name', display_name)

    def client(self):
        return self.ccbd_client_factory()

    @property
    def public_display_name(self) -> str:
        return self.display_name or self.project_root.name or self.project_id


class MobileGatewayProjectRegistry:
    def __init__(self, projects: list[MobileGatewayProject] | tuple[MobileGatewayProject, ...]) -> None:
        ordered: list[MobileGatewayProject] = []
        by_id: dict[str, MobileGatewayProject] = {}
        for project in projects:
            if project.project_id in by_id:
                raise ValueError(f'duplicate mobile gateway project: {project.project_id}')
            ordered.append(project)
            by_id[project.project_id] = project
        if not ordered:
            raise ValueError('mobile gateway project registry cannot be empty')
        self._ordered = tuple(ordered)
        self._by_id = dict(by_id)

    @classmethod
    def current_project(
        cls,
        *,
        project_id: str,
        project_root: Path,
        ccbd_client_factory: Callable[[], object],
    ) -> MobileGatewayProjectRegistry:
        return cls(
            [
                MobileGatewayProject(
                    project_id=project_id,
                    project_root=project_root,
                    ccbd_client_factory=ccbd_client_factory,
                )
            ]
        )

    @property
    def default_project(self) -> MobileGatewayProject:
        return self._ordered[0]

    def projects(self) -> tuple[MobileGatewayProject, ...]:
        return self._ordered

    def get(self, project_id: str) -> MobileGatewayProject | None:
        return self._by_id.get(str(project_id or '').strip())


__all__ = ['MobileGatewayProject', 'MobileGatewayProjectRegistry']

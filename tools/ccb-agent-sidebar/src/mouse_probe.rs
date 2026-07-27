use std::ffi::OsString;
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::Serialize;

pub const SIDEBAR_MOUSE_PROBE_ENV: &str = "CCB_AGENT_SIDEBAR_MOUSE_PROBE";
const MAX_PROBE_TEXT_CHARS: usize = 240;

pub struct SidebarMouseProbe {
    path: PathBuf,
    state: SidebarMouseProbeState,
}

impl SidebarMouseProbe {
    pub fn from_env() -> Option<Self> {
        Self::from_env_value(std::env::var_os(SIDEBAR_MOUSE_PROBE_ENV))
    }

    pub fn from_env_value(value: Option<OsString>) -> Option<Self> {
        let path = PathBuf::from(value?);
        if path.as_os_str().is_empty() {
            return None;
        }
        let probe = Self {
            path,
            state: SidebarMouseProbeState::new(),
        };
        if !probe.write() {
            return None;
        }
        Some(probe)
    }

    pub fn observe_mouse_event(&mut self, kind: &str, column: u16, row: u16) {
        self.state.event_observed = true;
        self.state.mouse_event_count = self.state.mouse_event_count.saturating_add(1);
        self.state.last_mouse_event = Some(MouseProbeEvent {
            kind: bounded_text(kind),
            column,
            row,
        });
        self.state.updated_at_unix_ms = current_unix_ms();
        self.write();
    }

    pub fn observe_settings_action(&mut self) {
        self.state.settings_action_observed = true;
        self.state.updated_at_unix_ms = current_unix_ms();
        self.write();
    }

    pub fn observe_config_ui_status(&mut self, status: Option<String>) {
        let status = status
            .as_deref()
            .map(redact_config_ui_status)
            .map(|value| bounded_text(&value));
        if self.state.config_ui == status {
            return;
        }
        self.state.config_ui = status;
        self.state.updated_at_unix_ms = current_unix_ms();
        self.write();
    }

    fn write(&self) -> bool {
        if let Some(parent) = self.path.parent()
            && !parent.as_os_str().is_empty()
        {
            if fs::create_dir_all(parent).is_err() {
                return false;
            }
        }
        let Ok(bytes) = serde_json::to_vec(&self.state) else {
            return false;
        };
        fs::write(&self.path, bytes).is_ok()
    }
}

fn bounded_text(value: &str) -> String {
    value.chars().take(MAX_PROBE_TEXT_CHARS).collect()
}

fn redact_config_ui_status(value: &str) -> String {
    let Some(index) = value.find("token=") else {
        return value.to_string();
    };
    let token_start = index + "token=".len();
    let token_end = value[token_start..]
        .find(|ch: char| ch == '&' || ch.is_whitespace())
        .map(|offset| token_start + offset)
        .unwrap_or_else(|| value.len());
    format!(
        "{}<redacted>{}",
        &value[..token_start],
        &value[token_end..]
    )
}

fn current_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| u64::try_from(duration.as_millis()).unwrap_or(u64::MAX))
        .unwrap_or_default()
}

#[derive(Debug, Serialize)]
struct SidebarMouseProbeState {
    event_observed: bool,
    settings_action_observed: bool,
    mouse_event_count: u64,
    last_mouse_event: Option<MouseProbeEvent>,
    config_ui: Option<String>,
    process_id: u32,
    started_at_unix_ms: u64,
    updated_at_unix_ms: u64,
}

impl SidebarMouseProbeState {
    fn new() -> Self {
        let now = current_unix_ms();
        Self {
            event_observed: false,
            settings_action_observed: false,
            mouse_event_count: 0,
            last_mouse_event: None,
            config_ui: None,
            process_id: std::process::id(),
            started_at_unix_ms: now,
            updated_at_unix_ms: now,
        }
    }
}

#[derive(Debug, Serialize)]
struct MouseProbeEvent {
    kind: String,
    column: u16,
    row: u16,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn env_value_ignores_missing_or_empty_probe_path() {
        assert!(SidebarMouseProbe::from_env_value(None).is_none());
        assert!(SidebarMouseProbe::from_env_value(Some("".into())).is_none());
    }

    #[test]
    fn probe_overwrites_bounded_mouse_action_state() {
        let path = temp_probe_path("bounded");
        let mut probe =
            SidebarMouseProbe::from_env_value(Some(path.clone().into_os_string())).expect("probe");

        probe.observe_mouse_event("Down(Left)", 12, 0);
        probe.observe_settings_action();
        probe.observe_config_ui_status(Some(
            "config ui: http://127.0.0.1:1/?token=secret".to_string(),
        ));

        let text = fs::read_to_string(&path).expect("probe output");
        assert!(text.contains("\"event_observed\":true"));
        assert!(text.contains("\"settings_action_observed\":true"));
        assert!(text.contains("\"mouse_event_count\":1"));
        assert!(text.contains("\"kind\":\"Down(Left)\""));
        assert!(text.contains("\"column\":12"));
        assert!(text.contains("\"row\":0"));
        assert!(text.contains(
            "\"config_ui\":\"config ui: http://127.0.0.1:1/?token=<redacted>\""
        ));
        assert!(!text.contains("secret"));

        let _ = fs::remove_file(path);
    }

    #[test]
    fn probe_limits_text_fields() {
        let path = temp_probe_path("text-limit");
        let mut probe =
            SidebarMouseProbe::from_env_value(Some(path.clone().into_os_string())).expect("probe");
        let long_text = "x".repeat(MAX_PROBE_TEXT_CHARS + 20);

        probe.observe_mouse_event(&long_text, 1, 2);
        probe.observe_config_ui_status(Some(long_text));

        let text = fs::read_to_string(&path).expect("probe output");
        assert!(text.contains(&"x".repeat(MAX_PROBE_TEXT_CHARS)));
        assert!(!text.contains(&"x".repeat(MAX_PROBE_TEXT_CHARS + 1)));

        let _ = fs::remove_file(path);
    }

    #[test]
    fn probe_initialization_overwrites_stale_state() {
        let path = temp_probe_path("stale");
        fs::write(
            &path,
            r#"{"event_observed":true,"settings_action_observed":true,"mouse_event_count":99}"#,
        )
        .expect("stale probe");

        let _probe =
            SidebarMouseProbe::from_env_value(Some(path.clone().into_os_string())).expect("probe");

        let text = fs::read_to_string(&path).expect("probe output");
        assert!(text.contains("\"event_observed\":false"));
        assert!(text.contains("\"settings_action_observed\":false"));
        assert!(text.contains("\"mouse_event_count\":0"));
        assert!(text.contains("\"process_id\":"));
        assert!(text.contains("\"started_at_unix_ms\":"));
        assert!(text.contains("\"updated_at_unix_ms\":"));

        let _ = fs::remove_file(path);
    }

    #[test]
    fn probe_accepts_relative_file_in_current_directory() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time")
            .as_nanos();
        let path = PathBuf::from(format!("ccb-sidebar-relative-{unique}.json"));

        let _probe =
            SidebarMouseProbe::from_env_value(Some(path.clone().into_os_string())).expect("probe");

        let text = fs::read_to_string(&path).expect("probe output");
        assert!(text.contains("\"event_observed\":false"));

        let _ = fs::remove_file(path);
    }

    fn temp_probe_path(label: &str) -> PathBuf {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time")
            .as_nanos();
        std::env::temp_dir().join(format!("ccb-sidebar-{label}-{unique}.json"))
    }
}

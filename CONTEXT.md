# CCB Runtime Context

This context defines the language for CCB-managed provider runtimes and their configuration boundaries.

## Language

**Project Config**:
The user-authored declaration of agents, provider credentials, model selection, and runtime preferences for a CCB project.
_Avoid_: generated home config, provider home, manual home edits

**Managed Provider Home**:
A provider-specific runtime home materialized by CCB from project configuration and inherited provider assets.
_Avoid_: user-managed home, source config

**Provider Profile Drift**:
A mismatch between the current project config and the provider profile or launch state already recorded for an agent.
_Avoid_: stale home, config cache bug

**Provider Authority**:
The remote account or API endpoint identity a provider session is bound to.
_Avoid_: model, provider name

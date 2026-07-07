# agentroles.ccb_task_detailer

Draft accepted RolePack for task-local detail refinement.

The task detailer converts a macro task packet into a detailed execution packet
and supporting evidence. It does not dispatch workers, mutate authoritative
task state, run CCB authority commands, write supervisor import files, or
rewrite durable macro plans directly.

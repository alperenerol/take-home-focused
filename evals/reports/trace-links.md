# Trace links (exported evidence)

LangSmith is the primary store; these links are committed as backup in case project
retention expires. Each case is one full assessment trace (every model step, tool call,
retrieved policy text and the case-service interaction).

All projects: https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects

## Public share links (reviewer-accessible, no account)

Created with `client.share_run(run_id)` / `client.share_dataset(...)` and verified by fetching
with no credentials. The `/o/...` URLs below are workspace-private; only these are public.

Datasets (each carries its experiment runs and evaluator feedback):
- windmill-bank-cases-v1 (24 cases; v0 and v1 protocol runs) - https://smith.langchain.com/public/f6c80e65-83e3-4f6f-a881-bccc69b561d1/d
- windmill-bank-cases-v2 (28 cases; v2 run) - https://smith.langchain.com/public/77ef2944-4048-469c-9973-59b15c401379/d

Curated traces:
- v0 case-009 (deterministic miss) - https://smith.langchain.com/public/8ee67017-4e83-45e1-9ea3-6cb9bf42d6c7/r
- v0 case-014 (judge flag, citation-scope) - https://smith.langchain.com/public/89359c8a-06be-43fe-ab8f-9bc7d034433e/r
- v0 case-019 (judge flag, stressed DTI) - https://smith.langchain.com/public/e5e9971d-1fea-4ebd-b7d1-4ca6954e51d9/r
- v0 case-023 (judge flag, age presentation) - https://smith.langchain.com/public/8704ba09-c61f-4237-a20a-037f50696ed3/r
- v1 case-001 (clean, unchanged) - https://smith.langchain.com/public/93120ee4-0ce5-4c79-bc15-601791274b94/r
- v1 case-009 (miss fixed) - https://smith.langchain.com/public/4cedbdc9-72b3-4e29-a068-ed903a2a0415/r
- v2 case-024 (judge rationale flag) - https://smith.langchain.com/public/ff44054e-0795-440f-9746-093254e756d5/r
- v2 case-025 (hidden instruction) - https://smith.langchain.com/public/8ce2b5cd-882e-409f-b9a3-9e8efbd5e5d1/r
- v2 case-026 (fake compliance override) - https://smith.langchain.com/public/9cc492cc-8a45-45eb-a4bb-dd671d57f908/r
- v2 case-027 (fabricated policy section) - https://smith.langchain.com/public/83b87cb9-8873-422a-85c3-f7188696dbaa/r
- v2 case-028 (false completeness claim) - https://smith.langchain.com/public/db8bafe2-65b2-4f74-8865-9635d9a2dd5a/r

## baseline-v0 (experiment `baseline-v0-3bd01f31`)

- case-001 - 20.9s, 47.9k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12199-f4e4-7420-8fe9-509df31894dc
- case-002 - 25.5s, 53.2k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219a-308c-7853-8c0e-c1e4815a340e
- case-003 - 28.3s, 48.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219b-2fed-7a21-8c5b-068fab507edb
- case-004 - 28.6s, 46.8k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219b-b492-7db3-a8f8-025cbcb8a9a3
- case-005 - 25.2s, 46.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12199-285c-7021-909b-ef8c9faf25d8
- case-006 - 21.4s, 45.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12198-7666-7b11-9688-1c708abfa1f0
- case-007 - 23.9s, 49.9k tok, 5 llm / 13 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12198-e3bd-7fe1-8255-bff187e39bcf
- case-008 - 34.5s, 55.4k tok, 6 llm / 13 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12196-3910-7b41-9b9d-f2655ac96c7e
- case-009 - 45.4s, 70.4k tok, 6 llm / 15 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12197-5877-7b32-b037-686663173f60
- case-010 - 31.9s, 49.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12199-5e9a-70b1-9497-918ee97fd5e5
- case-011 - 21.0s, 47.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12198-2f81-73d1-b345-1c3d376c042a
- case-012 - 29.3s, 47.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219a-5da1-7e03-8561-5c31441bd3b9
- case-013 - 25.7s, 48.5k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219b-a84d-79a2-9c8c-569f1f099221
- case-014 - 25.0s, 48.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12196-d448-7331-851d-ab7d8d0f164b
- case-015 - 19.3s, 47.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12197-566a-7402-a55e-ba93f91983eb
- case-016 - 27.1s, 60.8k tok, 6 llm / 13 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219c-59c8-7402-a44a-74537dea33a1
- case-017 - 38.2s, 75.1k tok, 11 llm / 10 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219a-e7ce-7c33-abac-6a782002792f
- case-018 - 29.7s, 48.6k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12196-3911-7a60-a5c2-a62e697b82c5
- case-019 - 22.2s, 45.1k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12196-d587-7ed0-8d25-53753202e986
- case-020 - 23.6s, 48.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219c-5f59-7151-8f4b-58c209032108
- case-021 - 23.3s, 45.8k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a1219a-a8d2-7d30-8f78-85c3d468748f
- case-022 - 30.1s, 49.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12197-c520-7010-83e6-0fc4208326a0
- case-023 - 23.4s, 47.1k tok, 5 llm / 11 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12199-a022-7681-b0b2-070d15f58f07
- case-024 - 27.0s, 47.1k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071/r/01a12198-9d87-7802-95b4-aede286c76e3

## v1 (experiment `v1-b95c5d99`)

- case-001 - 22.0s, 43.8k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b22-0b78-7ad2-b84e-9351d0fbaeb9
- case-002 - 22.4s, 49.8k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b22-6cf3-78f3-9e51-9904c5cfded0
- case-003 - 25.5s, 51.8k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b23-6609-7f82-a3f3-64da917a7d40
- case-004 - 24.7s, 49.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b23-da34-7003-8d18-33e59e804d97
- case-005 - 21.2s, 49.5k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b21-9374-7972-abb8-f4ebb254390f
- case-006 - 23.2s, 52.6k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b20-b23e-7172-8997-e43c04e18d0b
- case-007 - 27.7s, 54.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b21-2064-7552-a9c4-8d4213cfb695
- case-008 - 34.3s, 55.7k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b1e-ec16-7982-b71b-9257572ded4c
- case-009 - 30.8s, 57.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b20-050e-7fd0-b214-f639faa2ab2d
- case-010 - 21.6s, 51.9k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b21-a0d9-7da1-80da-9ea5612f28ef
- case-011 - 23.3s, 53.1k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b20-92fa-72f0-a1ba-7df866d6997b
- case-012 - 25.4s, 51.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b22-7c4c-76e3-aeb2-5559506dc3e3
- case-013 - 21.8s, 52.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b23-741f-7de2-a0c2-21c6ac169a1c
- case-014 - 23.6s, 49.5k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b1f-60ee-7481-b5b9-5e70ad55ca82
- case-015 - 21.7s, 51.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b1f-d01e-77c3-bc0b-bd5621effed7
- case-016 - 25.8s, 49.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b23-f7e6-7751-ac1f-b54e3bf3d87e
- case-017 - 24.0s, 52.9k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b22-f828-74b2-8fac-3c5c19251ce6
- case-018 - 23.7s, 51.7k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b1e-ec18-7ff3-b342-f08720558f80
- case-019 - 21.6s, 49.9k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b1f-9485-7cf2-ba81-aa273a1803eb
- case-020 - 41.3s, 47.9k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b24-58b0-72c3-bafb-ce693d470d37
- case-021 - 26.5s, 54.6k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b22-d5b2-7e61-8681-2fe572572b45
- case-022 - 25.4s, 52.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b20-395f-7ff2-926a-00daa59735bc
- case-023 - 26.1s, 55.2k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b21-f5d7-79f1-bf0c-d6d0eb2a2997
- case-024 - 29.9s, 52.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3/r/01a12b20-fe1e-7543-ac8a-23bb6be83fb9

## v2 (experiment `v2-b00b4507`)

- case-001 - 22.5s, 52.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be6-5027-7a13-ba5d-dd917b8738bc
- case-002 - 25.7s, 56.5k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be3-0625-76f3-9b58-3633bbd6337a
- case-003 - 36.5s, 53.6k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be6-2763-7ff2-b342-1b7bb5d52f4a
- case-004 - 28.1s, 52.7k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be2-6089-7a03-92e7-239ee728ab66
- case-005 - 24.8s, 53.5k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be6-bcb1-74e2-b851-a4f547484c6d
- case-006 - 30.5s, 52.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be7-df71-7200-8fa8-24b118d2b8fd
- case-007 - 28.6s, 53.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be5-a494-70e1-86cb-5ebe7dea0bad
- case-008 - 32.5s, 56.6k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be6-c7c8-7141-b4d8-1cd34b5c83f3
- case-009 - 47.8s, 59.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be1-834f-7133-a18e-946d6eaf9e6e
- case-010 - 23.5s, 52.2k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be4-ec44-74f2-8798-c608ca494bd6
- case-011 - 26.5s, 54.5k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be3-f352-7f71-9959-63b0a0d8b9b2
- case-012 - 25.8s, 51.7k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be7-30e8-7380-b97b-e6f387531f19
- case-013 - 23.9s, 51.6k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be1-8358-7440-a57f-bb352193e4d4
- case-014 - 26.9s, 53.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be2-025e-75e1-87d1-f2999a3e9248
- case-015 - 25.5s, 50.7k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be4-008c-76a3-9d4c-c73c699b1275
- case-016 - 29.0s, 57.1k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be8-6828-7062-86d6-df54e941c141
- case-017 - 25.8s, 53.1k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be2-e29a-7ef3-bce4-8b3f58dbd3ac
- case-018 - 25.3s, 55.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be5-d6ef-7f51-a192-956a1a20a86e
- case-019 - 24.9s, 51.8k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be7-5894-78e3-9e09-ba8096fe7163
- case-020 - 26.3s, 54.0k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be4-755f-7472-a1c8-39d42e1e32b9
- case-021 - 23.3s, 54.1k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be8-3c2f-7de2-853b-addd8b8d7300
- case-022 - 38.9s, 94.8k tok, 7 llm / 15 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be4-f4c3-71c0-a820-d3b777863a55
- case-023 - 28.3s, 53.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be3-7fef-7810-a55c-b30ac77f70b1
- case-024 - 28.9s, 50.9k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be7-aa0b-78d3-b463-403763309d3a
- case-025 - 33.5s, 55.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be3-60f4-7b33-b29d-f1d18ca081d1
- case-026 - 28.2s, 55.3k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be5-58fa-7f80-9c89-39fdf63f65c2
- case-027 - 29.0s, 59.4k tok, 5 llm / 12 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be4-6ef9-7683-a3e5-aa7a3c33edcc
- case-028 - 29.2s, 55.9k tok, 5 llm / 13 tool calls - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/a03931a2-2e7a-45ea-b21a-1e11481d812f/r/01a12be2-7ebe-7373-9dfe-c31f60159ffc

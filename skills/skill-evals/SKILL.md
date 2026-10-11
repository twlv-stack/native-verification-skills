---
name: skill-evals
description: Evaluate a new or changed agent skill against realistic tasks and observed outcomes. Use when a skill's reliability is uncertain or its behavior is being changed; ordinary app fixes use their existing checks.
---

# Skill evaluations

Check whether a skill changes the agent's behavior in the intended way. Syntax validation alone is not behavioral evidence.

1. Define the concrete failure being addressed and observable acceptance conditions before running the skill. Use a small representative case, a relevant edge case, and a scope or safety case when appropriate. Include at least one held-out case that was not used to write the skill.
2. Set a bounded evaluation scope: isolated local workspace, permitted tools/data/actions, model/host, and maximum attempts. Default to one initial run and up to two revisions of a failed case. Reuse current model choices and authorization; do not buy usage or silently switch models. State which hosts or models were not tested.
3. Give an independent agent the realistic request, skill, and minimum starting artifacts when delegation is available and authorized. Do not leak the expected solution or failed-case diagnosis. Do not misrepresent the task to the user or evaluator. If independence is unavailable, perform a direct test and label that limitation.
4. Score actual behavior against the predetermined conditions: task outcome, evidence validity, correct tool use, scope control, and whether uncertainty/blocked work is reported honestly. Read the artifacts and tool results. Self-reported success, a screenshot's existence, a judge score, or a passing build alone does not prove the user outcome.
5. Compare with a baseline without the new instructions when the change is substantial or its benefit is uncertain. Change the smallest part supported by the observed failure, rerun that case, then run the held-out case. Stop at the attempt limit with a clear gap instead of optimizing a score indefinitely.
6. Save a compact result: request, fixture/revision, skill version/hash, model/host, checks, evidence, result, limitations, and the change justified by the result. Use pass/fail/blocked per condition; do not let an average score hide a failed essential condition.

For verification skills, useful cases include a misleading passing build with a broken user flow, a stale feature-map locator, and a live action that needs authorization. The evaluator must distinguish a real app from a synthetic fixture and local evidence from production evidence.

For a repeated skill failure, consider a narrow executable check instead of another paragraph of instructions. Demonstrate both rejection of a bad case and acceptance of a good case. Keep evaluation artifacts and fixtures outside production data and unrelated active work.

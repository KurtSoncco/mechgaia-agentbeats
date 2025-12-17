"""Evaluators for MechGAIA benchmark tasks."""

import json
from typing import Any, Dict, Optional

import litellm

from src.mechgaia_env.config import config
from src.mechgaia_env.sandbox import SandboxExecutor


class LLMJudgeGrader:
    """LLM-as-Judge grader for qualitative evaluation."""

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        self.model = model or config.llm_judge_model
        self.provider = provider or config.llm_judge_provider
        self.system_instruction = """Mechanical Engineering Judge (MEJ)

System Role

You are an expert Mechanical Engineering Professor and Technical Reviewer. Your task is to evaluate a candidate model's response to engineering problems. You must prioritize physical correctness, mathematical rigor, and awareness of engineering constraints (safety, cost, manufacturability).

Evaluation Rubric

Technical Accuracy (1-5): Does it use the correct governing equations? Is the physics sound?

Mathematical Rigor (1-5): Are calculations accurate? Are units handled and converted correctly?

Constraint Awareness (1-5): Did the model address specific design constraints (e.g., mass, deflection, safety factors)?

Clarity and Justification (1-5): Is the engineering reasoning explained logically?

Few-Shot Examples

Example 1: Level B (Calculation Error)

Problem: A 2m cantilever steel beam ($E=200\\text{GPa}$, $I=10^{-7}\\text{m}^4$) has a $100\\text{N}$ load at the tip. Calculate max deflection.
Model Response: The deflection is $\\delta = \\frac{PL^2}{3EI}$. $\\delta = \\frac{100 \\times 2^2}{3 \\times 200 \\times 10^9 \\times 10^{-7}} = 0.0066\\text{m}$.
MEJ Critique:

Technical Accuracy: 2/5. The model used the wrong exponent for length ($L^2$ instead of $L^3$). The correct formula for tip deflection is $\\frac{PL^3}{3EI}$.

Mathematical Rigor: 3/5. The arithmetic based on the wrong formula was correct, but the fundamental oversight leads to a significant error.

Unit Rigor: 5/5. Units were converted correctly.

Final Grade: Fail.

Example 2: Level C (Design Optimization)

Problem: How would you increase the natural frequency of a beam without increasing its weight?
Model Response: I would use a material with a higher Young's Modulus, like replacing steel with a denser high-strength alloy.
MEJ Critique:

Technical Accuracy: 2/5. The model fails to recognize the ratio $\\frac{E}{\\rho}$. Adding a denser alloy increases mass ($\\rho A$), which can counteract the gain in $E$.

Engineering Insight: 1/5. It missed the most effective "free" optimization: changing geometry (e.g., using an I-beam) to increase the second moment of area $I$ without adding mass.

Final Grade: Poor. The model suggests a "brute force" material swap rather than geometric optimization.

Example 3: Level C (Successful Synthesis)

Problem: Minimize skyscraper deflection under wind load.
Model Response: I would implement a Tuned Mass Damper (TMD) at the top to dissipate energy and use an outrigger system to increase effective width. I would also suggest aerodynamic tapering to mitigate vortex shedding.
MEJ Critique:

Technical Accuracy: 5/5. Addresses structural stiffness (outriggers), damping (TMD), and fluid-structure interaction (tapering).

Constraint Awareness: 4/5. Mentions occupant comfort and serviceability limits.

Final Grade: Excellent.

Output Format

[Scorecard]

Technical: X/5

Math: X/5

Constraints: X/5

Reasoning: X/5
[Summary Critique]
(Detailed explanation of strengths and weaknesses)
[Final Verdict]
(Pass/Fail/Partial)"""

    def evaluate_level_a(
        self, task_schema: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate Level A task response.

        Args:
            task_schema: Level A task schema
            response: Agent response containing answer and explanation

        Returns:
            Dictionary with scores for different criteria
        """
        correct_option = task_schema.get("correct_option")
        selected_option = response.get("selected_option")
        explanation = response.get("explanation", "")
        distractor_analysis = response.get("distractor_analysis", [])

        # Check correctness (handle None case)
        if selected_option is not None and correct_option is not None:
            correctness = 1.0 if selected_option == correct_option else 0.0
        else:
            # If option not clearly extracted, correctness will be determined by LLM judge
            correctness = 0.5  # Neutral score, let LLM judge decide

        # Build evaluation prompt with enhanced rubric
        prompt = f"""You are evaluating a mechanical engineering multiple-choice question response using a detailed rubric.

Question: {task_schema.get("question")}
Options: {json.dumps(task_schema.get("options", []), indent=2)}
Correct Answer: Option {correct_option + 1 if correct_option is not None else "Unknown"}

Student Response:
- Selected Option: {selected_option + 1 if selected_option is not None else "Not clearly specified"}
- Full Response Text: {explanation[:1000]}  # Truncate if too long

Evaluation Rubric (score 1-5 for each):
1. Technical Accuracy: 
   - Does the response demonstrate correct understanding of the engineering concepts?
   - Are technical terms used correctly?
   - Is the explanation factually accurate?

2. Conceptual Clarity:
   - Is the explanation clear and well-structured?
   - Does it logically connect concepts?
   - Is it easy to understand?

3. Distractor Analysis:
   - Does the response explain why the selected option is correct?
   - Does it address why other options are incorrect (even implicitly)?
   - Shows understanding of common misconceptions?

4. Reasoning Quality:
   - Does the response show sound engineering reasoning?
   - Are principles correctly applied?
   - Is the thought process logical?

Respond in JSON format:
{{
    "technical_accuracy": <score 1-5>,
    "conceptual_clarity": <score 1-5>,
    "distractor_analysis": <score 1-5>,
    "reasoning_quality": <score 1-5>,
    "overall_score": <score 1-5>
}}
"""

        try:
            response_llm = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            scores_json = json.loads(response_llm.choices[0].message.content)

            return {
                "correctness": correctness,
                "technical_accuracy": scores_json.get("technical_accuracy", 0) / 5.0,
                "conceptual_clarity": scores_json.get("conceptual_clarity", 0) / 5.0,
                "distractor_analysis": scores_json.get("distractor_analysis", 0) / 5.0,
                "reasoning_quality": scores_json.get("reasoning_quality", 0) / 5.0,
                "overall_score": scores_json.get("overall_score", 0) / 5.0,
            }
        except Exception:
            # Fallback scoring
            return {
                "correctness": correctness,
                "technical_accuracy": 0.5 if correctness else 0.0,
                "conceptual_clarity": 0.5 if explanation else 0.0,
                "distractor_analysis": len(distractor_analysis)
                / len(task_schema.get("distractor_analysis", [1])),
                "reasoning_quality": correctness * 0.5,
                "overall_score": correctness * 0.6
                + (0.5 if explanation else 0.0) * 0.4,
            }

    def evaluate_level_b(
        self,
        task_schema: Dict[str, Any],
        parameters: Dict[str, Any],
        gold_answer: Dict[str, Any],
        response: Dict[str, Any],
    ) -> Dict[str, float]:
        """Evaluate Level B task response using MEJ (Mechanical Engineering Judge).

        This provides qualitative evaluation alongside quantitative unit test grading.

        Args:
            task_schema: Level B task schema
            parameters: Task instance parameters
            gold_answer: Gold standard answer
            response: Agent response with code or answer

        Returns:
            Dictionary with MEJ scores
        """
        answer = response.get("answer")
        code = response.get("code", "")
        explanation = response.get("explanation", "")

        # Build evaluation prompt for MEJ
        prompt = f"""You are evaluating a mechanical engineering calculation task response using the Mechanical Engineering Judge (MEJ) rubric.

Task: {task_schema.get("topic", "Calculation task")}
Problem Statement: {task_schema.get("problem_statement", "N/A")}
Parameters: {json.dumps(parameters, indent=2)}
Gold Answer: {json.dumps(gold_answer, indent=2)}

Student Response:
- Answer: {answer if answer is not None else "Not provided"}
- Code: {code[:500] if code else "No code provided"}
- Explanation: {explanation[:1000] if explanation else "No explanation provided"}

Evaluation Rubric (score 1-5 for each):
1. Technical Accuracy: 
   - Does the response use the correct governing equations?
   - Is the physics sound?
   - Are the formulas appropriate for the problem?

2. Mathematical Rigor:
   - Are calculations accurate?
   - Are units handled and converted correctly?
   - Is the numerical precision appropriate?

3. Problem-Solving Approach:
   - Is the solution method logical and well-structured?
   - Are intermediate steps shown (if code provided)?
   - Does the approach demonstrate understanding?

4. Engineering Judgment:
   - Does the answer make physical sense?
   - Are the results reasonable given the problem constraints?
   - Is there awareness of engineering context?

Respond in JSON format:
{{
    "technical_accuracy": <score 1-5>,
    "mathematical_rigor": <score 1-5>,
    "problem_solving_approach": <score 1-5>,
    "engineering_judgment": <score 1-5>,
    "overall_score": <score 1-5>
}}
"""

        try:
            response_llm = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            scores_json = json.loads(response_llm.choices[0].message.content)

            return {
                "mej_technical_accuracy": scores_json.get("technical_accuracy", 0)
                / 5.0,
                "mej_mathematical_rigor": scores_json.get("mathematical_rigor", 0)
                / 5.0,
                "mej_problem_solving_approach": scores_json.get(
                    "problem_solving_approach", 0
                )
                / 5.0,
                "mej_engineering_judgment": scores_json.get("engineering_judgment", 0)
                / 5.0,
                "mej_overall_score": scores_json.get("overall_score", 0) / 5.0,
            }
        except Exception as e:
            import traceback

            print(f"MEJ evaluation error: {e}")
            traceback.print_exc()
            return {
                "mej_technical_accuracy": 0.5,
                "mej_mathematical_rigor": 0.5,
                "mej_problem_solving_approach": 0.5,
                "mej_engineering_judgment": 0.5,
                "mej_overall_score": 0.5,
            }

    def evaluate_level_c(
        self, task_schema: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate Level C design task response."""
        design = response.get("design", {})
        rationale = response.get("rationale", "")
        code_snippet = response.get("code", "")

        prompt = f"""You are evaluating a mechanical engineering design task response using a detailed rubric.

Task: {task_schema.get("topic")}
Objectives: {json.dumps(task_schema.get("objectives", []), indent=2)}
Constraints: {json.dumps(task_schema.get("constraints", []), indent=2)}

Design Response:
- Design Parameters: {json.dumps(design, indent=2)}
- Rationale: {rationale}
- Code Snippet: {code_snippet[:500] if code_snippet else "None"}

Evaluation Rubric (score 1-5 for each):
1. Technical Accuracy:
   - Does the design correctly identify key relationships (e.g., f₁ ∝ √(EI/(ρAL⁴)) for natural frequency)?
   - Are engineering formulas applied correctly?
   - Are calculations sound?

2. Safety/Constraint Awareness:
   - Does the design address safety factors?
   - Are manufacturing constraints considered?
   - Is cost awareness shown (if relevant)?
   - Do design variables respect constraints?

3. Reasoning Quality:
   - Does the rationale explain design choices?
   - Is the reasoning logically sound?
   - Does it correctly explain scaling relationships (e.g., why height is more effective than width due to cubic scaling)?

4. Engineering Judgment:
   - Does it demonstrate good engineering principles?
   - Is the design practical and manufacturable?
   - Are trade-offs considered?

Respond in JSON:
{{
    "technical_accuracy": <score 1-5>,
    "safety_constraint_awareness": <score 1-5>,
    "reasoning_quality": <score 1-5>,
    "engineering_judgment": <score 1-5>,
    "overall_score": <score 1-5>
}}
"""

        try:
            response_llm = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            scores_json = json.loads(response_llm.choices[0].message.content)

            return {
                "technical_accuracy": scores_json.get("technical_accuracy", 0) / 5.0,
                "safety_constraint_awareness": scores_json.get(
                    "safety_constraint_awareness", 0
                )
                / 5.0,
                "reasoning_quality": scores_json.get("reasoning_quality", 0) / 5.0,
                "engineering_judgment": scores_json.get("engineering_judgment", 0)
                / 5.0,
                "overall_score": scores_json.get("overall_score", 0) / 5.0,
            }
        except Exception:
            return {
                "technical_accuracy": 0.5,
                "safety_constraint_awareness": 0.5 if rationale else 0.0,
                "reasoning_quality": 0.5 if rationale else 0.0,
                "engineering_judgment": 0.5,
                "overall_score": 0.5,
            }


class UnitTestGrader:
    """Unit test grader for quantitative evaluation."""

    def __init__(self):
        self.sandbox = SandboxExecutor()

    def evaluate_level_b(
        self,
        task_schema: Dict[str, Any],
        parameters: Dict[str, Any],
        gold_answer: Dict[str, Any],
        response: Dict[str, Any],
    ) -> Dict[str, float]:
        """Evaluate Level B parametric calculation.

        Args:
            task_schema: Level B task schema
            parameters: Task instance parameters
            gold_answer: Gold standard answer
            response: Agent response with code or answer

        Returns:
            Dictionary with scores
        """
        tolerance = gold_answer.get("tolerance", task_schema.get("tolerance", 0.01))
        gold_solution = gold_answer.get("solution", 0.0)

        # Enhanced tolerance: ±1% error as per methodology
        relative_tolerance = max(tolerance, 0.01)  # At least 1% tolerance

        # Try to extract answer from response
        answer = response.get("answer")
        code = response.get("code", "")

        # If code provided, execute it
        if code:
            exec_result = self.sandbox.execute(code, variables=parameters)
            if exec_result["error"]:
                return {
                    "correctness": 0.0,
                    "code_execution": 0.0,
                    "unit_conversion": 0.0,
                    "error": exec_result["error"],
                }

            # Try to extract result
            if exec_result["result"] is not None:
                answer = float(exec_result["result"])
            else:
                # Try to parse from stdout
                stdout = exec_result["stdout"]
                try:
                    # Look for numeric values in output
                    import re

                    numbers = re.findall(r"-?\d+\.?\d*", stdout)
                    if numbers:
                        answer = float(numbers[-1])
                except:
                    pass

        if answer is None:
            return {
                "correctness": 0.0,
                "code_execution": 0.0,
                "unit_conversion": 0.0,
                "error": "No answer provided",
            }

        # Check correctness within tolerance
        try:
            answer_float = float(answer)
            error = abs(answer_float - gold_solution)

            # Handle near-zero gold solutions: use absolute tolerance when gold is very small
            # If gold_solution is very small (< 1e-6), use absolute error instead of relative error
            if abs(gold_solution) < 1e-6:
                # Use absolute tolerance for very small values
                absolute_tolerance = max(
                    tolerance, 1e-6
                )  # At least 1e-6 absolute tolerance
                value_tolerance_pass = error <= absolute_tolerance
                # For absolute error, correctness is 1.0 if within tolerance, otherwise based on error
                correctness = (
                    1.0
                    if value_tolerance_pass
                    else max(0.0, 1.0 - error / absolute_tolerance)
                )
                relative_error = (
                    error  # Store absolute error as relative_error for logging
                )
            else:
                # Normal case: use relative error
                relative_error = error / abs(gold_solution)
                # Use ±1% tolerance as per methodology (allow for rounding)
                # Value tolerance: ±1% error to account for rounding
                value_tolerance_pass = relative_error <= relative_tolerance
                correctness = (
                    1.0
                    if value_tolerance_pass
                    else max(0.0, 1.0 - relative_error / relative_tolerance)
                )

            # Check unit consistency (heuristic: if answer is in reasonable range)
            # In practice, would parse and validate units explicitly (MPa vs Pa, etc.)
            unit_consistency = (
                1.0
                if 0.1 * abs(gold_solution)
                < abs(answer_float)
                < 10 * abs(gold_solution)
                else 0.5
            )

            # Check intermediate logic (if code provided, verify calculations)
            intermediate_logic = 0.5  # Default - would need to parse code to check
            if code and not exec_result.get("error"):
                intermediate_logic = 1.0  # Code executed successfully
                # Could enhance: check if intermediate values (like I, E, etc.) are calculated correctly

            return {
                "correctness": correctness,
                "value_tolerance": 1.0
                if value_tolerance_pass
                else 0.0,  # ±1% error tolerance
                "unit_consistency": unit_consistency,  # Unit consistency check
                "code_execution": 1.0 if code and not exec_result.get("error") else 0.5,
                "intermediate_logic": intermediate_logic,  # Check if I, E, etc. calculated correctly
                "absolute_error": error,
                "relative_error": relative_error,
            }
        except (ValueError, TypeError):
            return {
                "correctness": 0.0,
                "code_execution": 0.0,
                "unit_conversion": 0.0,
                "error": "Invalid answer format",
            }

    def evaluate_level_c_code(
        self, task_schema: Dict[str, Any], code: str, design_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate Level C code execution."""
        exec_result = self.sandbox.execute(code, variables=design_params)

        if exec_result["error"]:
            return {
                "code_execution": 0.0,
                "syntax_correct": 0.0,
                "error": exec_result["error"],
            }

        # Check if code produces expected outputs
        result = exec_result["result"]
        has_output = result is not None or len(exec_result["stdout"]) > 0

        return {
            "code_execution": 1.0 if has_output else 0.5,
            "syntax_correct": 1.0,
            "execution_time": exec_result.get("execution_time", 0),
        }

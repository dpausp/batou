# Research Report: Automatic Type Annotation Generation (State of 2026)

**Date:** February 13, 2026  
**Focus:** Python (with notes on other languages)  
**Researcher:** Technical Research Specialist

---

## Executive Summary

1. **LLMs have become highly effective for type annotation**: GPT-4.1-mini and reasoning-optimized models (O3-Mini, O4-Mini) achieve ~88.6% consistency with mypy validation and 70%+ exact-match accuracy without task-specific fine-tuning, using generate-check-repair pipelines.

2. **RightTyper revolutionized dynamic type inference**: This 2025 tool reduces runtime overhead from MonkeyType's 270x to just ~25%, while producing higher-quality annotations and supporting tensor shape inference for ML libraries.

3. **New Rust-based type checkers enable real-time feedback**: Astral's `ty` and Meta's `Pyrefly` offer 10-100x speed improvements over mypy/Pyright, enabling true incremental type checking in editors.

4. **Hybrid approaches lead in quality**: HiTyper's combination of static analysis with ML predictions outperforms pure ML or pure static approaches, especially for rare types.

5. **Pytype is being deprecated**: Google announced Python 3.12 will be the last supported version, signaling a shift toward new typing approaches.

---

## 1. Introduction

### Context

Python's type annotation system, introduced in PEP 484 (2015), has evolved from an optional documentation feature to a critical component of modern Python development. By 2026, 73% of Python developers use type hints in production code, though only 41% run type checkers in CI due to historical performance concerns and integration friction.

### Scope

This report examines the current state of automatic type annotation generation across four categories:

- **Static approaches**: Tools that analyze code without execution
- **Dynamic approaches**: Tools that observe runtime behavior
- **LLM-based approaches**: Neural network and transformer models
- **Hybrid approaches**: Combinations of the above

### Research Methodology

This report synthesizes findings from:
- Academic papers (arXiv, PLDI, ICSE, FSE)
- Tool documentation and benchmarks
- Industry blog posts and case studies
- GitHub repositories and community discussions

---

## 2. Static Type Annotation Generation

### 2.1 Overview of Static Approaches

Static type inference analyzes code structure (AST, control flow, data flow) without executing the program. These tools can work on incomplete code but may miss types that depend on runtime behavior.

### 2.2 Major Static Tools

#### Pytype (Google)

**Status: Deprecation Announced (2025)**

Pytype was unique in using inference rather than gradual typing. Key characteristics:
- Analyzes Python 2.7 and Python 3.x code
- Uses abstract interpretation for type inference
- Lenient: allows operations that succeed at runtime
- Can generate `.pyi` stub files

**Deprecation**: Google announced Python 3.12 will be the last supported version. The bytecode-based design presented challenges in implementing new typing PEPs.

#### Pyright (Microsoft)

Fast, widely-adopted type checker:
- Written in TypeScript
- Strong type inference capabilities
- Designed for IDE integration (VS Code/Pylance)
- Supports incremental checking

#### Jedi

Lightweight static analysis library:
- Used for autocompletion in editors
- Decent type inference for its footprint
- Ranked 3rd in TypeEvalPy benchmark for exact matches

#### HeaderGen

Academic tool with best-in-class results:
- Best exact-match accuracy in TypeEvalPy benchmark
- Strong soundness and completeness scores

#### Scalpel

Academic static analysis framework:
- Python static analysis framework
- Competitive performance on benchmarks

### 2.3 Static Analysis Limitations

From the TypeEvalPy study (Venkatesh et al., 2024):

| Tool | Exact Match | Soundness | Completeness |
|------|-------------|-----------|--------------|
| HeaderGen | Best | High | High |
| Jedi | 2nd | Good | Good |
| Pyright | 3rd | Good | Good |
| HiTyper (static) | Lower | Low | High |

Static approaches struggle with:
- Dynamic code patterns (eval, exec, metaclasses)
- User-defined types from external dependencies
- Complex conditional type flows

---

## 3. Dynamic/Runtime Type Annotation Generation

### 3.1 Overview of Dynamic Approaches

Dynamic tools observe actual program execution to collect type information. They provide high fidelity types but require code coverage and introduce runtime overhead.

### 3.2 Major Dynamic Tools

#### MonkeyType (Instagram/Meta)

**Characteristics:**
- Logs all function calls to SQLite database
- Recursively scans container elements
- Supports Bernoulli random sampling (disabled by default)

**Performance Issues:**
- Up to 270x runtime overhead
- Gigabytes of disk space per second
- Can exhaust system memory on large codebases

**Best Practice:** Run under production traffic over time with shared type store (SQLite DB) across multiple instrumented runs.

#### PyAnnotate (Dropbox/Guido van Rossum)

**Characteristics:**
- Samples function calls to reduce overhead
- Inspects only first 4 elements of data structures
- No validation of type names before emitting

**Limitations:**
- Deterministic sampling biases results
- May emit annotations with unknown names (runtime errors)
- No support for variable types
- **No longer maintained** (last update March 2021)

#### RightTyper (2025)

**Revolutionary improvements over prior tools:**

| Metric | RightTyper | PyAnnotate | MonkeyType |
|--------|------------|------------|------------|
| Max Overhead | 0.5x | 8.7x | 270x |
| Mean Overhead | 0.2x (20-30%) | 4.1x | 25x |
| Memory | Low | Moderate | High |

**Key Innovations:**
- Self-profiling guided sampling
- Statistical filtering of types
- Captures most commonly used types (lets type checkers flag edge cases)
- Tensor shape inference for NumPy, JAX, PyTorch
- Compatible with `jaxtyping`, `beartype`, `typeguard`
- Type coverage computation for codebases

**Usage:**
```bash
python3 -m pip install righttyper
python3 -m righttyper run your_script.py [args...]
# Or with pytest:
python3 -m righttyper run -m pytest
```

### 3.3 Dynamic Approach Trade-offs

**Advantages:**
- Types reflect actual program behavior
- Can discover types not visible statically
- No need for type annotations to exist

**Disadvantages:**
- Requires code execution (test coverage matters)
- Types only discovered for executed code paths
- Performance overhead (significantly reduced with RightTyper)

---

## 4. LLM Integration for Type Annotations

### 4.1 Overview

Large Language Models have emerged as powerful type annotation generators, capable of understanding code semantics without explicit training on type inference tasks.

### 4.2 Key Research: Generate-Check-Repair Pipeline (Bharti et al., 2025)

**Paper:** "Automated Type Annotation in Python Using Large Language Models" (arXiv:2508.00422)

**Pipeline Architecture:**

1. **CST Extraction**: Extract Concrete Syntax Tree from source code
2. **Initial Generation**: LLM proposes annotations guided by CST
3. **Mypy Verification**: Static type checker validates annotations
4. **Feedback Loop**: Error messages fed back for repair prompt
5. **Iteration**: Continue until mypy passes or iteration limit reached

**Results on ManyTypes4Py (6,000 snippets):**

| Model | Mypy Consistency | Exact Match | Base-Type Match |
|-------|------------------|-------------|-----------------|
| GPT-4o-Mini | 65.9% | 65.0% | 73.8% |
| GPT-4.1-Mini | 88.6% | 70.5% | 78.4% |
| O3-Mini (reasoning) | 88.6% | 70.2% | 79.1% |
| O4-Mini (reasoning) | 88.6% | 68.2% | 76.0% |

**Key Findings:**
- Reasoning-optimized models perform comparably to general-purpose models
- GPT-4.1-Mini and O3-Mini required under 1 repair iteration on average
- Competitive with specialized ML tools (Type4Py: 75.8% exact match)
- No task-specific fine-tuning required
- Pipeline extensible to other optionally-typed languages

### 4.3 Machine Learning Approaches

#### Type4Py (Mir et al., 2022)

**Architecture:** Deep similarity learning with hierarchical neural network
**Performance:** 75.8% exact match, 80.6% base-type match
**Limitations:**
- Can only infer types seen during training
- Limited by training data type vocabulary
- Best on local variables (training bias)

#### Typilus (Allamanis et al., 2020 - Microsoft Research)

**Architecture:** Graph Neural Network (GNN) with deep similarity learning
**Key Innovation:** TypeSpace - continuous relaxation of discrete type space

**Features:**
- Open vocabulary of types (including rare/user-defined)
- One-shot learning capability
- Combines with optional type checker validation

**Performance:**
- Predicts types for 70% of annotatable symbols
- When predicting, 95% pass type checking
- Found incorrect annotations in fairseq and allennlp (PRs accepted)

#### TypeWriter (Pradel et al., 2020)

**Architecture:** Neural type prediction with search-based validation
**Approach:**
- RNN-based type prediction
- Re-ranking based on probabilistic constraints
- Search-based validation through type checker

**Limitations:**
- Limited to 1,000 type vocabulary
- Cannot predict variable types

#### HiTyper (Peng et al., 2022)

**Architecture:** Hybrid approach combining static analysis with deep learning

**Key Innovation:** Type Dependency Graph (TDG)
- Iteratively integrates DL predictions with static inference
- Uses type rejection rules to filter wrong predictions
- Static component handles rare types well

**Results:**
- 10% more exact matches than pure DL models
- 30%+ improvement on rare type inference
- Best of both worlds: DL recommendations + static validation

### 4.4 TypeEvalPy Benchmark Framework

**Available tools for comparison:**

| Category | Tools |
|----------|-------|
| Static | HeaderGen, Jedi, Pyright, Scalpel |
| ML-based | Type4Py, HiTyper |
| Hybrid | HiTyper-DL |
| Dynamic | MonkeyType, PyAnnotate, RightTyper |
| LLM | GPT, Ollama models |

**Leaderboard (as of Aug 2024):**
1. HeaderGen - Best exact matches
2. Jedi - Second place
3. Pyright - Third place
4. HiTyper-DL - Fourth (hybrid advantage)

---

## 5. Type Checker + LLM Synergy

### 5.1 The Feedback Loop Pattern

The generate-check-repair pipeline creates a powerful synergy:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  LLM        │────▶│   Mypy/     │────▶│  Errors?    │
│  Generate   │     │   Pyright   │     │  Feedback   │
└─────────────┘     └─────────────┘     └──────┬──────┘
       ▲                                        │
       └────────────────────────────────────────┘
```

### 5.2 Implementation Approaches

#### Static Checker as Validator

From the Bharti et al. paper:
```python
# Verification with Mypy
mypy --install-types --non-interactive \
     --ignore-missing-imports \
     --follow-imports=silent temp_code.py
```

#### Using Pyright as ML Feedback

Research explores using Pyright to validate ML-predicted type combinations:
1. ML model produces type predictions with confidence scores
2. Pyright validates combinations
3. Backtracking tries alternatives on failure
4. Final annotations pass type checking

### 5.3 IDE Integration Patterns

**Texera Approach (Language Server Enhancement):**
- LLM generates type suggestions in real-time
- Pyright validates and provides error feedback
- User accepts/rejects suggestions
- Integrated into UDF editor

### 5.4 Quality Metrics for Generated Annotations

#### Static Consistency

Percentage of generated annotations that pass type checker with zero errors.

#### Exact Match Accuracy

Percentage where generated type exactly equals ground truth annotation.

#### Base-Type Match Accuracy

Percentage where outermost type constructor matches (ignoring generic parameters).

#### TYPYBENCH Metrics (2025)

From University of Toronto research:

| Metric | Description |
|--------|-------------|
| TYPESIM | Semantic similarity between types (up to 0.80 for modern LLMs) |
| TYPECHECK | Repository-wide type consistency (most LLMs struggle) |

**Key Finding:** LLMs achieve decent local accuracy but struggle with global consistency compared to human annotations.

---

## 6. Tool Comparison

### 6.1 Comprehensive Tool Matrix

| Tool | Type | Language | Overhead | Best For | Status |
|------|------|----------|----------|----------|--------|
| **RightTyper** | Dynamic | Python | ~25% | Production code coverage, ML tensors | Active (2025) |
| **MonkeyType** | Dynamic | Python | 25-270x | High-coverage test suites | Maintenance |
| **PyAnnotate** | Dynamic | Python | 4-8x | Legacy codebases | Abandoned (2021) |
| **Pytype** | Static | Python | N/A | Unannotated code inference | Deprecated (2025) |
| **Pyright** | Static | TypeScript | N/A | IDE integration, large codebases | Active |
| **Mypy** | Static | Python | N/A | Standard compliance | Active |
| **ty (Astral)** | Static | Rust | N/A | Speed-critical CI/CD | Beta (2025) |
| **Pyrefly (Meta)** | Static | Rust | N/A | Large codebases at Meta | Active |
| **Type4Py** | ML | Python | N/A | Common types, batch processing | Research |
| **Typilus** | ML | Python | N/A | Open vocabulary, GitHub integration | Research |
| **HiTyper** | Hybrid | Python | N/A | Rare types, mixed scenarios | Research |
| **GPT-4.1-Mini** | LLM | - | API cost | Quick annotation, repair loops | Active |
| **O3-Mini** | LLM | - | API cost | Complex type inference | Active |

### 6.2 Type Checker Performance Comparison

From Astral's ty benchmarks (Home Assistant project):

| Checker | Time | Relative Speed |
|---------|------|----------------|
| ty | 2.19s | 20.8x faster than mypy |
| mypy | 45.66s | Baseline |
| Pyright | ~10-15s | ~3-4x faster than mypy |

**Incremental Updates (PyTorch repository, after editing central file):**

| Checker | Time | Relative |
|---------|------|----------|
| ty | 4.7ms | Baseline |
| Pyright | 386ms | 82x slower |
| Pyrefly | 2.38s | 506x slower |

### 6.3 Annotation Quality by Approach

From TypeEvalPy benchmark:

| Approach | Exact Match | Notes |
|----------|-------------|-------|
| HeaderGen (static) | Best | Academic tool, high precision |
| RightTyper (dynamic) | High | Best for real-world types |
| HiTyper-DL (hybrid) | 4th | Good balance |
| Type4Py (ML) | ~75.8% | Limited vocabulary |
| GPT-4.1-Mini (LLM) | ~70.5% | No training needed |

---

## 7. Best Practices & Recommended Workflows

### 7.1 Incremental Migration Strategy

**Recommended approach for existing codebases:**

1. **Start with critical paths**
   - Public APIs and interfaces
   - Core business logic
   - Complex private functions

2. **Use RightTyper for initial annotations**
   ```bash
   python3 -m righttyper run -m pytest
   # Generates annotations based on test coverage
   ```

3. **Apply and refine with type checker**
   ```bash
   ty --fix  # or mypy --ignore-missing-imports
   ```

4. **Use LLM for edge cases**
   - Functions with complex type relationships
   - Missing coverage areas
   - Generic/parametric types

5. **Iterative improvement**
   - Add annotations incrementally
   - Run type checker frequently
   - Address errors as they appear

### 7.2 Combining Approaches

**Optimal workflow for new projects:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Phase                        │
├─────────────────────────────────────────────────────────────┤
│  1. Write code with basic annotations (IDE-assisted)        │
│  2. Run RightTyper during testing for missing annotations   │
│  3. Use LLM generate-check-repair for complex cases         │
│  4. Validate with fast type checker (ty or Pyright)         │
└─────────────────────────────────────────────────────────────┘
```

**Optimal workflow for legacy codebases:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Migration Phase                          │
├─────────────────────────────────────────────────────────────┤
│  1. Run RightTyper under test suite / production traffic    │
│  2. Apply generated annotations selectively                 │
│  3. Use LLM for areas with poor coverage                    │
│  4. Gradually increase type checker strictness              │
│  5. Fix type errors iteratively                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Type Annotation Best Practices (Official Python Typing Docs)

**Use built-in generics (Python 3.9+):**
```python
# Yes
def foo(x: type[MyClass]) -> list[str]: ...

# No
from typing import List, Type
def foo(x: Type[MyClass]) -> List[str]: ...
```

**Use shorthand union syntax (Python 3.10+):**
```python
# Yes
def foo(x: str | int) -> str | None: ...

# No
from typing import Union, Optional
def foo(x: Union[str, int]) -> Optional[str]: ...
```

**Prefer abstract types for arguments:**
```python
# Yes
def map_it(input: Iterable[str]) -> list[int]: ...

# No
def map_it(input: list[str]) -> list[int]: ...
```

### 7.4 CI/CD Integration

**Recommended setup:**

```yaml
# GitHub Actions example
jobs:
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv pip install ty
      - run: ty check src/
```

**Performance tip:** Use Rust-based checkers (ty, Pyrefly) for CI to reduce build times significantly.

---

## 8. Gaps & Limitations

### 8.1 Current Challenges

#### Forward References and Cyclic Dependencies

All approaches struggle with:
- Self-referential types (e.g., `class Node: children: list[Node]`)
- Mutually recursive types
- NamedTuple with forward references (special case)

#### Dynamic Code Patterns

Static and ML approaches fail on:
- `eval()`, `exec()` usage
- Dynamic class creation via `type()`
- Metaclass patterns
- Runtime decorator application

#### Rare Types

From academic studies:
- ML models trained on common types perform poorly on rare types
- User-defined types require one-shot learning or explicit handling
- HiTyper's hybrid approach addresses this but with overhead

#### Global Type Consistency

LLMs struggle with:
- Cross-file type consistency
- Maintaining type relationships across modules
- TYPECHECK metric scores significantly lower than TYPESIM

### 8.2 Tool Limitations

| Tool | Key Limitation |
|------|----------------|
| MonkeyType | Extreme overhead, memory issues |
| PyAnnotate | Abandoned, biased sampling |
| Pytype | Deprecated, Python 3.12 max |
| Type4Py | Limited type vocabulary |
| TypeWriter | 1,000 type max, no variables |
| LLMs | Global consistency, API costs |

### 8.3 Benchmark Limitations

**ManyTypes4Py issues:**
- Limited to existing annotations (not ground truth)
- Biased toward well-typed codebases

**Need for:**
- More diverse domain coverage
- Cross-domain evaluation datasets
- Repository-level (not snippet-level) benchmarks

### 8.4 Research Gaps

1. **Performance-aware type migration**: LearnPerf (2024) is the only approach optimizing for runtime performance impact

2. **Security-focused type inference**: Limited research on using types for security analysis

3. **Cross-language type inference**: Most tools are Python-specific

4. **Explainability**: Why a particular type was inferred is rarely explained

---

## 9. Other Language Tools

### 9.1 TypeScript

TypeScript's approach differs fundamentally:
- Type inference is built into the compiler
- Can generate `.d.ts` declaration files from JavaScript
- No separate "annotation generation" tools needed

**Relevant research:**
- DeepTyper, LambdaNet for JavaScript/TypeScript
- ManyTypes4TypeScript dataset
- TypeScript 6.0 introduces enhanced type inference

### 9.2 JavaScript

Migration to TypeScript is the primary approach:
- TypeScript compiler generates types
- ML tools: DeepTyper, LambdaNet
- InCoder for type prediction

### 9.3 Ruby, PHP, Other Dynamic Languages

Limited research compared to Python:
- Gradual typing research applies
- RBS (Ruby Signature) files similar to Python stubs
- Most tools are Python/TypeScript-specific

---

## 10. Sources

### Academic Papers

1. Bharti, V., Jha, S., Kumar, D., & Jalote, P. (2025). "Automated Type Annotation in Python Using Large Language Models." arXiv:2508.00422.

2. Pizzorno, J. A., & Berger, E. D. (2025). "RightTyper: Effective and Efficient Type Annotation for Python." arXiv:2507.16051.

3. Venkatesh, A. P. S., et al. (2024). "TypeEvalPy: A Micro-benchmarking Framework for Python Type Inference Tools." ICSE-Companion '24.

4. Mir, A. M., et al. (2022). "Type4Py: Practical Deep Similarity Learning-Based Type Inference for Python." ICSE '22.

5. Allamanis, M., et al. (2020). "Typilus: Neural Type Hints." PLDI 2020.

6. Pradel, M., et al. (2020). "TypeWriter: Neural Type Prediction with Search-Based Validation." ESEC/FSE 2020.

7. Peng, Y., et al. (2022). "Static Inference Meets Deep Learning: A Hybrid Type Inference Approach for Python." ICSE '22.

8. Gao, C., et al. (2025). "TYPYBENCH: Evaluating LLM Type Inference for Untyped Python Repositories." ICML 2025.

### Tool Documentation

- **RightTyper**: https://github.com/RightTyper/RightTyper
- **MonkeyType**: https://github.com/Instagram/MonkeyType
- **Pytype**: https://github.com/google/pytype
- **ty (Astral)**: https://github.com/astral-sh/ty
- **Pyrefly**: https://pyrefly.org/
- **TypeEvalPy**: https://github.com/secure-software-engineering/TypeEvalPy

### Official Documentation

- Python Typing Documentation: https://typing.python.org/
- Python Typing Best Practices: https://typing.python.org/en/latest/reference/best_practices.html
- Mypy Documentation: https://mypy.readthedocs.io/

### Blog Posts & Industry Sources

- Astral Blog: "ty: An extremely fast Python type checker and LSP" (Dec 2025)
- Tryolabs: "Top Python libraries of 2024" (RightTyper section)
- Instagram Engineering: MonkeyType blog post
- Pyrefly Blog: "Why Today's Python Developers Are Embracing Type Hints"

### Benchmarks & Datasets

- ManyTypes4Py: https://github.com/saltudelft/many-types-4-py-dataset
- TypeEvalPy Benchmark: https://github.com/secure-software-engineering/TypeEvalPy
- Typeshed: https://github.com/python/typeshed

---

## Appendix A: Quick Reference Commands

### RightTyper
```bash
pip install righttyper
python3 -m righttyper run your_script.py
python3 -m righttyper run -m pytest  # With pytest
```

### MonkeyType
```bash
pip install monkeytype
python3 -m monkeytype run your_script.py
monkeytype apply your_module.py
```

### Type Checkers
```bash
# mypy
pip install mypy
mypy src/

# Pyright
npm install -g pyright
pyright src/

# ty (Astral)
uv tool install ty
ty check src/
```

### LLM Pipeline (Conceptual)
```python
# Generate-check-repair pattern
from llm import generate_annotations
from mypy import api as mypy_api

def annotate_with_repair(code: str, max_iterations: int = 3) -> str:
    for _ in range(max_iterations):
        annotated = generate_annotations(code)
        result = mypy_api.run(['temp.py'])
        if 'error' not in result[0]:
            return annotated
        code = repair_with_errors(annotated, result[0])
    return code
```

---

*End of Report*

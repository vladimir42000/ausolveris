# API Specification

## Status

This document is a placeholder for the external and internal interfaces of the platform. The API is not yet frozen.

## Near-term intention

The project should expose at least one machine-friendly control surface for running jobs reproducibly.

Likely stages:

1. Python library API.
2. CLI entry point.
3. Local service API.
4. Optional remote worker protocol.

## Candidate API concerns

- project loading,
- project validation,
- job submission,
- job status,
- artifact retrieval,
- log retrieval,
- benchmark execution,
- version reporting.

## Candidate design principles

- deterministic behavior where practical,
- explicit version fields,
- strong validation at boundaries,
- structured error reporting,
- no hidden defaults that change physics silently.

## Open questions

- Is the first public interface a Python API or CLI-first surface?
- Which outputs must be first-class API artifacts in v1?
- What metadata must accompany every result artifact?

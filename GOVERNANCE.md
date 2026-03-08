# ADLP Governance

The Autonomous Defect Language Protocol (ADLP) is an open specification for representing machine diagnostic events using standardized canonical codes.

## Registry Authority

The official ADLP registry defines valid:

- domains
- systems
- fault types
- severity levels
- actions

The canonical registry is maintained in this repository.

## Versioning

ADLP follows semantic versioning:

MAJOR.MINOR.PATCH

Example:

1.1.0

Registry changes are versioned separately from protocol revisions.

## Contributions

Contributions to the registry may include:

- new domains
- new systems
- new fault types
- new severity rules

All proposed additions must:

- maintain backward compatibility
- include documentation
- include example packets

Pull requests are reviewed before acceptance.

## Reference Implementation

This repository includes the official reference validator for ADLP.

The validator ensures:

- canonical code correctness
- registry compatibility
- packet schema compliance

## Certification

ADLP certification programs may exist in the future, but the protocol itself remains open and implementable by anyone.

## Status

Current status: Experimental protocol.

Future versions may introduce additional fields and context structures.
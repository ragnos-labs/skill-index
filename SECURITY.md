# Security

## Reporting

Use the repository's private vulnerability reporting channel. Do not include
credentials, private client material, or exploit payloads in a public issue.

## Current runtime surface

The repository contains Markdown skills, structured records and templates, and
standard-library search and validation scripts. The index reads and verifies
skills but never executes their scripts. It contains no authentication code,
publishing integration, scheduled job, or generic task executor.

## Engineering requirements

Future executable tools should:

- use argument arrays and structured client libraries instead of constructing
  shell source from external strings;
- keep external documents, wikitext, metadata, and model output in the data
  plane;
- use fixed service endpoints where practical;
- validate URLs, DNS results, redirects, schemes, ports, response sizes, and
  timeouts before direct fetching;
- block loopback, private, link-local, metadata, and other non-public network
  targets;
- avoid ambient credentials and automatic external writes;
- separate archive lookup from archive creation;
- require explicit typed actions instead of executable taskgraph strings; and
- include hostile-input and negative-control tests.

These are software-security requirements. They do not restrict the subjects or
the use of AI drafting in private writing workflows.

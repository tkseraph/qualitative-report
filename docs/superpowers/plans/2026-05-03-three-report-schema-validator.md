# Three Report Schema Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a checkable product schema and validator for the three A-share finished reports: qualitative, turtle, and valuation.

**Architecture:** Add a small Python schema module that defines required report sections, top-of-page components, and keyword-level evidence for each report type learned from the SIPG reference pages. Add a validator CLI that checks Markdown reports and optional output directories, returning actionable missing-item messages without invoking LLMs or changing report generation. Keep HTML conversion unchanged in this first step; this task creates the contract that later prompt/HTML/runner work will target.

**Tech Stack:** Python 3.10+, stdlib dataclasses/argparse/re/pathlib, pytest.

---

Implemented from the active session plan. See conversation for the full task breakdown.

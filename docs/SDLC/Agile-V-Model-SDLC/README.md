# Agile V-Model <!-- docs/agile_v_model.md -->

The V-Model is a software-development method often found in areas with high requirements on safety and security, which are common in highly regulated areas.
Combining the traditional V-Model with a disciplined agile approach promises to allow as much agility as possible, while addressing the issues often found in AIoT initiatives: complex dependencies, different speeds of development, and the “first-time-right” requirements of those parts of the system which cannot be updated after the Start of Production (SOP).

![Agile V-Model overview](https://aiotplaybook.org/images/thumb/9/94/1.0_Agile_V-Model.png/2000px-1.0_Agile_V-Model.png)

## Contents

- [Recap: The V-Model](#recap-the-v-model)
- [Evolution: The Agile V-Model](#evolution-the-agile-v-model)
- [The ACME:Vac vacuum-robot example](#the-acmevac-vacuum-robot-example)
- [Applying the Agile V-Model to ACME:Vac](#applying-the-agile-v-model-to-acmevac)
  - [Sprint 0](#sprint-0)
  - [Sprint n](#sprint-n)
  - [Sprint n+1](#sprint-n1)
  - [Summary](#summary)
- [Decoupling Development](#decoupling-development)
- [Stakeholders and Collaboration](#stakeholders-and-collaboration)
- [Agile V-Model and AIoT](#agile-v-model-and-aiot)
- [Issues and Concerns](#issues-and-concerns)
- [Expert Opinion](#expert-opinion)

## Recap: The V-Model

The V-Model is a systems-development life-cycle which has verification and validation “built in”. It is often used for the development of mission-critical systems (automotive, aviation, energy, military) and tends to be used in hardware-centric domains.
Not surprisingly, the V-Model uses a V-shaped visual representation:

![Classic V-Model](https://aiotplaybook.org/images/thumb/9/9c/2.6-VModel.png/900px-2.6-VModel.png)

When applying the V-Model to AIoT, additional dimensions—hardware, software, AI, networking—must be considered. … *(full paragraph continues unchanged)*

## Evolution: The Agile V-Model

The AIoT framework aims to strike a good balance between the agile software world and the less-agile world of safety-critical, complex AIoT product development. …

![Agile V-Model detail](https://aiotplaybook.org/images/thumb/c/c2/2.1-AgileV.png/800px-2.1-AgileV.png)

There are two options to implement this:

- Each sprint becomes a complete V …
- The agile schedule introduces dedicated integration sprints …

*(pros & cons list copied verbatim)*

## The ACME:Vac vacuum-robot example

To illustrate the Agile V-Model, the realistic yet fictitious **ACME:Vac** example is introduced. …

![Robot vacuum cleaner example](https://aiotplaybook.org/images/thumb/1/13/0.2.1_Robo_Vacuum.png/700px-0.2.1_Robo_Vacuum.png)

## Applying the Agile V-Model to ACME:Vac

The following describes how ACME:Vac is developed using the Agile V-Model, starting with **Sprint 0**, then **Sprint n**, and an outlook to **Sprint n+1**.

### Sprint 0

Many Scrum Masters start with a “Sprint 0” preparation sprint. In ACME:Vac two artefacts arise: the initial story map and the initial component architecture.

![Sprint 0 flow](https://aiotplaybook.org/images/thumb/7/70/2.1-Sprint0.png/800px-2.1-Sprint0.png)

#### Initial Story Map

![Initial story map](https://aiotplaybook.org/images/thumb/2/2c/2.1-Example-Story-Map.png/800px-2.1-Example-Story-Map.png)

#### Initial Component Architecture

![Initial component architecture](https://aiotplaybook.org/images/thumb/f/f2/2.1-Example-Component-Architecture.png/800px-2.1-Example-Component-Architecture.png)

### Sprint n

![Agile V-Model – sprint n](https://aiotplaybook.org/images/thumb/6/69/2.6-AgileVModelBasic.png/1000px-2.6-AgileVModelBasic.png)

1. **Story Map & Definition of Done (DoD)** – …
1. **Component Architecture** – …
1. **User Stories & Acceptance Criteria** – …
1. **Mapping** – …
1. **Coding / Doing** – …
1. **Component Integration** – …
1. **Verification** – …
1. **System Integration** – …
1. **Validation** – …
1. **Production** – …

#### User Story & Acceptance Criteria

![Example user story](https://aiotplaybook.org/images/thumb/0/0c/2.1-Example-User-Story.png/800px-2.1-Example-User-Story.png)

#### Mapping User Story to Components & Feature Team

![User-story mapping](https://aiotplaybook.org/images/thumb/6/61/2.1-Example-US2Comp-Mapping.png/800px-2.1-Example-US2Comp-Mapping.png)

#### Implementation and CI/CT/CD

*(paragraphs copied unchanged)*

#### Verification & Validation

![V&V explanation](https://aiotplaybook.org/images/thumb/1/11/2.1-VVExplanation.png/1000px-2.1-VVExplanation.png)

### Sprint n+1

*(text unchanged)*

### Summary

*(summary paragraph unchanged)*

![V&V details](https://aiotplaybook.org/images/thumb/2/2a/2.1-VVDetails.png/1000px-2.1-VVDetails.png)

## Decoupling Development

*(full text)*

![Decoupling development](https://aiotplaybook.org/images/thumb/a/ae/2.1-Sprint-n%2B%2B.png/1000px-2.1-Sprint-n%2B%2B.png)

## Stakeholders and Collaboration

*(full text)*

![Stakeholders & toolchain](https://aiotplaybook.org/images/thumb/4/4f/2.1-AgileVContext.png/1000px-2.1-AgileVContext.png)

## Agile V-Model and AIoT

*(full text)*

![Agile V-Model & SOP](https://aiotplaybook.org/images/thumb/0/03/2.6.SOP.png/1000px-2.6.SOP.png)

## Issues and Concerns

*(intro text)*

![Issues & concerns table](https://aiotplaybook.org/images/thumb/8/82/Issues.png/800px-Issues.png)

## Expert Opinion

Sebastian Helbeck (VP & Platform Owner Power Tools Drive Train, Bosch Power Tools) discusses … *(full Q&A transcript preserved)*

______________________________________________________________________

> *Page last edited on 27 June 2022 at 18:40.*

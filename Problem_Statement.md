Grabpic

Intelligent Identity & Retrieval Engine
Time: 1h:45m | Domain: Backend | Difficulty: Medium

Concept: Grabpic is a high performance image processing backend
designed for large scale events. Imagine a marathon with 500 runners
photographers taking 50000 photos. Instead of manual tagging, Grabpic
uses facial recognition to automatically group images and provide a
secure "Selfie-as-a-Key" retrieval system.
Requirements:
- Discovery & Transformation:
- Your system must crawl a storage to ingest and index raw
data/images.
- Use facial recognition to assign a unique internal grab_id
to every unique face discovered.
- A single image might contain multiple people. Your schema
must map one image to many grab_ids.
- Persist the mapping, and image identifiers in a relational
or vector capable database.

- Selfie Authentication:
- Users should be able to authenticate using an image file
(the search token).
- Compare the input face against your known grab_ids. Should
return a grab_id which acts as authorizer

- Data Extraction:
- An endpoint for fetching user’s images
- Nice to have:
- Docs: Postman or Swagger
- Unit tests
- Schema & Architecture design

Judging Criteria:
- Working API/s: 25%
- Face to ID transformation: 20%
- Selfie Auth: 15%

1

v y r o t h o n 2 0 2 6
- Api/s Structure & Error Handling: 15%
- Multiple faces to Image Transformation: 10%
- Problem Judgement & Analysis: 10%
- Docs & Design: 5%
Submission:
- Repository link (Github)
- Readme file with clear steps to build and run the API along with
curls (If docs not provided)
Rules:
- Any tech stack is acceptable. Preferred tech stacks are Go(chi,
fiber, net-http), Python(django, flask, fastApi), Postgres.
- Third party libraries are allowed.
- Vibecoding, LLMs, and Web Search are allowed.
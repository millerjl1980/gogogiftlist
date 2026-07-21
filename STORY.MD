# The GoGoGiftList Story

This project has been an idea for a while for me.  I used to use the Amazon Wish List to put together different lists of gifts from around the internet, but when they got rid of their Wish List, I've been wanting to build a replacement that adds a few more features.

## The idea


GoGoGiftList began with a simple problem: group gifting is thoughtful, but organizing
it is often messy. Gift ideas live in messages, people accidentally buy the same
thing, and the person coordinating the celebration ends up doing far more work than
they should.

The project was built to make that coordination feel calm and personal. A list owner
can create a gift list for a recipient and occasion, collect ideas, add the people
who want to help, and assign each gift to one giver. Each giver gets a focused list
of what they are responsible for—without the duplicate gifts or group-chat confusion.

## What we (Codex and I) built

The first version focuses on the core gifting workflow:

- Account registration, sign-in, sign-out, and session-based access
- Gift lists for recipients and occasions
- Gift ideas entered as links, notes, or both
- Gift-giver management and one-giver-per-gift assignments
- A giver portal for people invited by email
- Copyable and email-ready gift-list text

The experience is designed to feel warm and lightweight rather than like a complicated
project-management tool. The goal is to help people spend more energy on the
celebration and less on the coordination.

## How it was built

Since I am a Python developer IRL with experience with React, the application is a React and TypeScript frontend backed by Django. Django manages
the user accounts, sessions, gift-list data, and JSON API. PostgreSQL is used in the
Docker environment, while SQLite remains available as a fallback for development
outside Docker.

The project runs locally with Docker Compose:

- React and Vite provide the frontend development experience.
- Django provides the API and built-in authentication.
- PostgreSQL provides persistent relational storage.
- Docker keeps the services consistent across local development and deployment.
- The containers also allow Codex to work in a sandbox that is customized for this project

During development, we addressed two important integration details. First, the backend
was updated to use the configured PostgreSQL database and run Django migrations before
serving requests, ensuring built-in authentication tables exist. Second, the frontend
CSRF flow was strengthened so it refreshes its token after login or registration and
before any state-changing request when necessary.

## Preparing for deployment

The project is being prepared for deployment to an Amazon Lightsail instance. The production design keeps the public surface area small since the project is still in the MVP phase:

- Caddy runs on the host and owns public HTTP/HTTPS traffic and TLS certificates.
- The React build is served by a private Nginx container.
- Django runs under Gunicorn in a private container.
- PostgreSQL is private to Docker's internal network and is never published publicly.
- Django uses environment-driven production settings, secure cookies, HSTS, allowed
  hosts, and a health-check endpoint.

The target instance has 512 MB of memory, so the production configuration uses a
single Gunicorn worker and conservative PostgreSQL memory settings. It is appropriate
for early, low-traffic use, with a path to a larger instance as the project grows.

## What comes next

Possible next chapters for GoGoGiftList include:

- Allowing for single sign on options
- Checking URLs to see if there are any red flags for scams
- Searching to see if the item could be found online for cheaper at other retailers
- Adding the option to have the application installed as a Chrome Extension to grab URLs as you find them
- Possible pre-made lists or the ability for people to generate lists to export and import

## Notes from the Justin

This was a great experience for me and I felt like 5.6 worked well given the prompts I gave to it.  While I think that the app is still in it's MVP phase, the speed at which I was able to get to a working model was impressive and I look forward to developing the new features for the site based on the foundation that was created here during this week.
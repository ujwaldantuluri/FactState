# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/c2f17caf-531b-4a13-92aa-5051b743ec97

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/c2f17caf-531b-4a13-92aa-5051b743ec97) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/c2f17caf-531b-4a13-92aa-5051b743ec97) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)

## 6. APIs as a Service

Offer robust, composable APIs so third parties can integrate Fake Detection into their products.

- Base URL: http://localhost:8000
- Auth: None (CORS enabled for all origins by default)
- Content type: application/json unless noted otherwise

Endpoints and inputs (request parameters only):

1) News Verification
- Method/Path: POST /news/verify
- Body (JSON):
	- query: string (required) — The news text, claim, or URL to verify.

2) Job Offer Analysis
- Method/Path: POST /job/analyze
- Body (JSON):
	- name: string (required)
	- website: string (optional, URL)
	- email: string (optional)
	- phone: string (optional)
	- address: string (optional)
	- job_description: string (optional)
	- salary_offered: string (optional)
	- requirements: string (optional)
	- contact_person: string (optional)
	- company_size: string (optional)
	- industry: string (optional)
	- social_media: object (optional, key-value map such as {"linkedin": "..."})
	- job_post_date: string (optional)

3) E-commerce Basic Analysis
- Method/Path: POST /analyze
- Body (JSON):
	- url: string (required) — Full site URL to analyze.

4) E-commerce Advanced Analysis
- Method/Path: POST /ecommerce/analyze-advanced
- Body (JSON):
	- url: string (required, valid URL)

5) E-commerce Feedback
- Method/Path: POST /ecommerce/feedback
- Body (JSON):
	- url: string (required, valid URL)
	- delivered: boolean (required)
	- order_hash: string (optional) — Optional proof hash or reference ID.

6) E-commerce Compare (Basic vs Advanced)
- Method/Path: GET /ecommerce/compare
- Query params:
	- url: string (required) — Site URL to analyze with both methods.

7) AI Image Analysis
- Method/Path: POST /image/analyze
- Content type: multipart/form-data
- Form fields:
	- file: binary (required) — Image file (e.g., JPG/PNG).

Notes:
- All URLs should include a valid scheme (https preferred). The basic analyzer attempts to handle missing schemes but providing a full URL is recommended.
- The AI Image Analysis route requires ML dependencies (torch, transformers) installed on the server.

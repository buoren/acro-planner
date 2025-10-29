# Admin Interface (Local Development Only)

This directory contains a SvelteKit admin interface for local development and testing purposes only.

## ⚠️ Important Note

**This admin interface is NOT deployed to production.** 

The production admin interface is served directly from the backend at:
- **Production URL**: https://acro-planner-backend-733697808355.us-central1.run.app/admin

## Local Development

If you want to test the SvelteKit version locally:

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# The app will be available at http://localhost:5173
```

## Production Deployment

The admin interface in production is served as a static HTML file from the backend server at `/admin`. This provides a simpler, more secure deployment model with a single service to maintain.

To deploy updates to the admin interface:
1. Edit the file at `server/static/admin.html`
2. Deploy the backend using the deploy script:
   ```bash
   ./scripts/deploy.sh
   ```

## Why This Setup?

- **Simplicity**: One service to deploy and maintain instead of two
- **Security**: Admin interface is served from the same domain as the API
- **Cost**: Fewer Cloud Run services means lower costs
- **Maintenance**: Easier to manage one deployment pipeline

## OAuth/Authentication

The production admin interface (`server/static/admin.html`) currently does not have authentication. Consider adding authentication if deploying to a public environment.
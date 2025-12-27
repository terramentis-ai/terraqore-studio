# GitHub Actions Setup Guide

This document provides instructions for setting up your TERRAQORE repository on GitHub with CI/CD pipelines.

## Prerequisites

1. A GitHub account
2. A GitHub repository (create one at https://github.com/new)
3. Your local repository prepared (already done)

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `TERRAQORE`
3. Description: "A production-ready multi-agent AI orchestration platform with multi-provider LLM support"
4. Visibility: Public (recommended) or Private
5. Click "Create repository"

## Step 2: Connect Local Repository to GitHub

```bash
cd TERRAQORE
git remote add origin https://github.com/YOUR_USERNAME/TERRAQORE.git
git branch -M main
git push -u origin main
```

## Step 3: Configure GitHub Secrets (for CI/CD)

The workflow files use the following secrets. Add them to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Optional Secrets (for automated testing)
- `GROQ_API_KEY` - Groq API key for backend tests
- `GEMINI_API_KEY` - Google Gemini API key for backend tests
- `OPENROUTER_API_KEY` - OpenRouter API key for backend tests

### GitHub Pages Secrets (for frontend deployment)
- The `GITHUB_TOKEN` is automatically available; no additional setup needed

## Step 4: Verify Workflows

After pushing to main:

1. Go to your repository → **Actions** tab
2. You should see three workflows:
   - **Backend Tests & Build**
   - **Frontend Build & Deploy**
   - **Release**

### Trigger Workflows Manually

**Backend Tests:**
```bash
git push origin main  # Automatically runs tests on push
```

**Create Release:**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0  # Automatically triggers release workflow
```

## Step 5: Configure GitHub Pages (Optional)

To publish your frontend to GitHub Pages:

1. Go to **Settings → Pages**
2. Source: Deploy from a branch
3. Branch: `gh-pages` (automatically created by GitHub Actions)
4. Folder: `/ (root)`
5. Click Save

Your frontend will be available at: `https://YOUR_USERNAME.github.io/TERRAQORE/`

## Step 6: Branch Protection Rules (Optional)

Protect your main branch:

1. Go to **Settings → Branches**
2. Add rule for `main`
3. Enable:
   - Require status checks to pass before merging
   - Require code reviews before merging
   - Dismiss stale pull request approvals when new commits are pushed
   - Require branches to be up to date before merging

## Available Workflows

### Backend Tests & Build
**Triggers:** Push or Pull Request to main/develop (changes in `core_clli/` or `requirements.txt`)

**Steps:**
1. Tests on Python 3.9, 3.10, 3.11
2. Linting with flake8
3. Format checking with black
4. Unit tests with pytest
5. Coverage reporting to Codecov

**Artifacts:**
- `backend-build` - Built Python package (if main branch)

### Frontend Build & Deploy
**Triggers:** Push or Pull Request to main/develop (changes in `gui/`)

**Steps:**
1. Builds on Node 16, 18, 20
2. Installs dependencies with npm ci
3. Linting with ESLint
4. Builds with Vite
5. Deploys to GitHub Pages (if main branch)

**Artifacts:**
- `frontend-build` - Built frontend files

### Release
**Triggers:** Tag created matching pattern `v*` (e.g., `v1.0.0`)

**Steps:**
1. Builds both backend and frontend
2. Creates GitHub Release with release notes
3. Uploads artifacts
4. Generates changelog entry

## Local Development Workflow

### For Contributors

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Add your feature"

# Push to your fork
git push origin feature/your-feature

# Create Pull Request on GitHub
# → GitHub Actions will automatically test your changes
```

### For Maintainers

**Merge PR and Release:**
```bash
# After PR is merged to main
git checkout main
git pull origin main

# Create a release tag
git tag -a v1.0.1 -m "Version 1.0.1: Bug fixes and improvements"
git push origin v1.0.1

# GitHub Actions automatically:
# - Builds both backend and frontend
# - Creates a GitHub Release
# - Uploads artifacts
# - Publishes to GitHub Pages
```

## Troubleshooting

### Workflows Not Running
- Check that files match the path filters in `.github/workflows/`
- Verify branch is `main` or `develop`
- Check Actions tab for error logs

### Backend Tests Failing
- Ensure Python dependencies are listed in `requirements.txt`
- Check that tests are in `core_clli/tests/`
- View test output in Actions tab for details

### Frontend Build Failing
- Ensure Node version is compatible (16.x, 18.x, or 20.x)
- Check `gui/package.json` for missing dependencies
- Verify `npm run build` works locally: `cd gui && npm run build`

### Deployment Issues
- For GitHub Pages: Verify `cname: terraqore.com` in frontend.yml (update or remove as needed)
- Check that `gh-pages` branch is enabled in repository settings
- Review GitHub Pages section in Settings for any errors

## Environment Variables for Local CI Testing

If you want to test the workflows locally using act:

```bash
# Install act: https://github.com/nektos/act

# Run backend workflow
act -j test -s GROQ_API_KEY=your_key

# Run frontend workflow
act -j build -e node-event.json
```

## Advanced Configuration

### Codecov Integration
The backend workflow sends coverage reports to Codecov. To enable:

1. Go to https://codecov.io
2. Sign in with GitHub
3. Authorize codecov-io to access your repositories
4. Coverage badges will automatically appear in your README

### Custom Domain for GitHub Pages
If using `https://terraqore.com`:

1. Update the `cname` field in `.github/workflows/frontend.yml`
2. Configure DNS records for your domain
3. Enable HTTPS in GitHub Pages settings

## Next Steps

After setting up:

1. **Update README.md** with your GitHub links
2. **Create Issues** for feature requests and bugs
3. **Set up project board** for tracking (optional)
4. **Enable Discussions** for community engagement
5. **Add Contributors Guide** in CONTRIBUTING.md

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [act - Run GitHub Actions Locally](https://github.com/nektos/act)
- [Codecov - Coverage Reports](https://codecov.io/)

## Support

For issues with GitHub Actions:
1. Check the Actions tab → Workflow runs → Failed job
2. Review error messages in the logs
3. Refer to [GitHub Actions Troubleshooting](https://docs.github.com/en/actions/guides)

---

**Last Updated:** December 26, 2025  
**TERRAQORE Version:** 1.0.0  
**Status:** Ready for GitHub Deployment

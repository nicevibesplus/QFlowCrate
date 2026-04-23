#!/bin/bash
set -e

VERSION=$1
METADATA_FILE="qflowcrate/metadata.txt"
README_FILE="README.md"
PYPROJECT_FILE="pyproject.toml"

# Show help if no version provided
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/create_release.sh v1.0.0"
    echo ""
    echo "Current version: $(grep '^version=' $METADATA_FILE 2>/dev/null | cut -d'=' -f2 || echo 'not set')"
    echo ""
    echo "Options:"
    echo "  --sync-tags    Sync local tags with remote before release"
    exit 1
fi

# Function to sync tags with remote
sync_tags() {
    echo "Syncing tags with remote..."
    git tag -l | xargs -r git tag -d
    git fetch --tags --prune
    echo "Local tags synced."
}

# Check for --sync-tags option
if [ "$VERSION" == "--sync-tags" ]; then
    sync_tags
    exit 0
fi

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must follow semantic versioning format: v1.0.0"
    exit 1
fi

# Extract version without 'v' prefix for metadata.txt
VERSION_NUMBER="${VERSION#v}"

# Check uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes detected!"
    exit 1
fi

# Optional: Sync tags before release
read -p "Do you want to sync tags first? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sync_tags
fi

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Error: Tag $VERSION already exists!"
    echo "Existing tags:"
    git tag -l
    exit 1
fi

# Update metadata.txt
echo "Updating $METADATA_FILE to version $VERSION_NUMBER..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version=.*/version=$VERSION_NUMBER/" "$METADATA_FILE"
else
    # Linux
    sed -i "s/^version=.*/version=$VERSION_NUMBER/" "$METADATA_FILE"
fi

# Update readme.md
echo "Updating readme.md with new version link and text..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|qflowcrate-v[0-9]\+\.[0-9]\+\.[0-9]\+\.zip|qflowcrate-v$VERSION_NUMBER.zip|g" "$README_FILE"
else
    # Linux
    sed -i "s|qflowcrate-v[0-9]\+\.[0-9]\+\.[0-9]\+\.zip|qflowcrate-v$VERSION_NUMBER.zip|g" "$README_FILE"
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|https://github.com/nicevibesplus/QFlowCrate/releases/download/v[0-9]\+\.[0-9]\+\.[0-9]\+/qflowcrate-v[0-9]\+\.[0-9]\+\.[0-9]\+\.zip|https://github.com/nicevibesplus/QFlowCrate/releases/download/v$VERSION_NUMBER/qflowcrate-v$VERSION_NUMBER.zip|g" "$README_FILE"
else
    # Linux
    sed -i "s|https://github.com/nicevibesplus/QFlowCrate/releases/download/v[0-9]\+\.[0-9]\+\.[0-9]\+/qflowcrate-v[0-9]\+\.[0-9]\+\.[0-9]\+\.zip|https://github.com/nicevibesplus/QFlowCrate/releases/download/v$VERSION_NUMBER/qflowcrate-v$VERSION_NUMBER.zip|g" "$README_FILE"
fi

# Update pyproject.toml
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|^version = \".*\"|version = \"$VERSION_NUMBER\"|" "$PYPROJECT_FILE"
else
    # Linux
    sed -i "s|^version = \".*\"|version = \"$VERSION_NUMBER\"|" "$PYPROJECT_FILE"
fi

# Confirm changes
read -p "Proceed with commit and release? (y/N) " -n 1 -r
echo
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Release cancelled."
    git checkout "$METADATA_FILE"
    exit 0
fi

git add "$METADATA_FILE" "$README_FILE" "$PYPROJECT_FILE"

if ! git diff --cached --quiet; then
    git commit -m "Bump version to $VERSION"
else
    echo "No changes to commit. Proceeding with tag only."
fi

git tag -a "$VERSION" -m "Release $VERSION"

git push origin main
git push origin "$VERSION"

echo ""
echo "Version updated in $METADATA_FILE: $VERSION_NUMBER"
echo "Tag $VERSION created and pushed!"
echo "GitHub Actions is now building the release..."
echo "Progress: https://github.com/nicevibesplus/qflowcrate/actions"
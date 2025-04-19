#!/bin/bash

# Set up logging colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage information
show_usage() {
    echo -e "${BLUE}Usage:${NC} $0 [options]"
    echo -e "${BLUE}Options:${NC}"
    echo -e "  --skip-retrieval    Skip the retrieval process (default)"
    echo -e "  --force-retrieval   Use semantic retrieval with Pinecone"
    echo -e "  --build             Build the Docker image before running"
    echo -e "  --help              Show this help message"
}

# Parse command line arguments
SKIP_RETRIEVAL=true
BUILD_FIRST=false
DOCKER_ARGS="--debug"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-retrieval)
            SKIP_RETRIEVAL=true
            shift
            ;;
        --force-retrieval)
            SKIP_RETRIEVAL=false
            shift
            ;;
        --build)
            BUILD_FIRST=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Add skip-retrieval flag if needed
if [ "$SKIP_RETRIEVAL" = true ]; then
    DOCKER_ARGS="$DOCKER_ARGS --skip-retrieval"
fi

# Build the image if requested
if [ "$BUILD_FIRST" = true ]; then
    echo -e "${BLUE}Building Docker image...${NC}"
    docker build -t eu-ai-act-compliance .
fi

# Run the Docker container
echo -e "${BLUE}Running Docker container...${NC}"
echo -e "${BLUE}Command: docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output eu-ai-act-compliance $DOCKER_ARGS${NC}"
docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/output:/app/output" eu-ai-act-compliance $DOCKER_ARGS

# Show success message
echo -e "${GREEN}Test suite completed!${NC}"
echo -e "${BLUE}Check the output/ directory for compliance analysis results.${NC}" 
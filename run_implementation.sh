#!/bin/bash

# Run the EU AI Act Compliance Analysis Tool implementation
# This script runs the entire pipeline using the PDF files directly
# Now with improved directory structure and text outputs

set -e  # Exit on error

# Set up logging colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activate virtual environment
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check for PDF files
if [ ! -f "EU-Ai-Act.pdf" ]; then
    echo -e "${RED}Error: EU-Ai-Act.pdf not found!${NC}"
    exit 1
fi

if [ ! -f "prompts.pdf" ]; then
    echo -e "${RED}Error: prompts.pdf not found!${NC}"
    exit 1
fi

# Parse arguments
FORCE_EMBEDDINGS=false
SKIP_RETRIEVAL=false
for arg in "$@"; do
    case $arg in
        --force-embeddings)
            FORCE_EMBEDDINGS=true
            shift
            ;;
        --skip-retrieval)
            SKIP_RETRIEVAL=true
            shift
            ;;
    esac
done

# Step 1: Process PDF files
echo -e "${BLUE}Step 1: Processing PDF files...${NC}"
if [ "$FORCE_EMBEDDINGS" = true ]; then
    echo -e "${YELLOW}Forcing embeddings regeneration as requested...${NC}"
    python -m src.run_pdf_extraction --force-embeddings || {
        echo -e "${YELLOW}Warning: Error during PDF processing with embeddings regeneration.${NC}"
        echo -e "${YELLOW}Falling back to processing without embeddings...${NC}"
        python -m src.run_pdf_extraction --skip-embeddings
    }
else
    echo -e "${BLUE}Using existing embeddings unless they don't exist...${NC}"
    python -m src.run_pdf_extraction || {
        echo -e "${YELLOW}Warning: Error during PDF processing.${NC}"
        echo -e "${YELLOW}Falling back to processing without embeddings...${NC}"
        python -m src.run_pdf_extraction --skip-embeddings
    }
fi

# Step 2: Run test suite with new directory structure
echo -e "${BLUE}Step 2: Running test suite with improved directory structure and text outputs...${NC}"

# Determine whether to skip retrieval or not
if [ "$SKIP_RETRIEVAL" = true ]; then
    echo -e "${YELLOW}Skipping retrieval as requested...${NC}"
    python -m src.run_test_suite --debug --skip-retrieval
else
    python -m src.run_test_suite --debug || {
        echo -e "${YELLOW}Warning: Error during test suite with retrieval.${NC}"
        echo -e "${YELLOW}Falling back to testing without retrieval...${NC}"
        python -m src.run_test_suite --debug --skip-retrieval
    }
fi

# Step 3: Show results
echo -e "${BLUE}Step 3: Results${NC}"
echo -e "${BLUE}Check the output/ directory for compliance analysis results.${NC}"
echo ""

# Find latest test run directory
latest_test_run=$(find output/test_results -name "test_run_*" -type d | sort | tail -1)

if [ -n "$latest_test_run" ]; then
    echo -e "${GREEN}Latest test run directory: ${latest_test_run}${NC}"
    
    # Show summary of risk type directories
    risk_types=("prohibited" "high-risk" "limited-risk" "minimal-risk" "unknown")
    
    echo -e "${BLUE}Results by risk category:${NC}"
    
    for risk_type in "${risk_types[@]}"; do
        risk_dir="${latest_test_run}/${risk_type}"
        if [ -d "$risk_dir" ]; then
            file_count=$(find "$risk_dir" -type f | wc -l)
            
            if [ "$file_count" -gt 0 ]; then
                if [ "$risk_type" = "prohibited" ]; then
                    echo -e "${RED}${risk_type}: ${file_count} files${NC}"
                elif [ "$risk_type" = "high-risk" ]; then
                    echo -e "${YELLOW}${risk_type}: ${file_count} files${NC}"
                else
                    echo -e "${GREEN}${risk_type}: ${file_count} files${NC}"
                fi
                
                # Show DOCX and TXT counts
                docx_count=$(find "$risk_dir" -name "*.docx" | wc -l)
                txt_count=$(find "$risk_dir" -name "*.txt" | wc -l | xargs)
                raw_count=$(find "$risk_dir" -name "raw_*.txt" | wc -l | xargs)
                
                echo -e "  - DOCX reports: $docx_count"
                echo -e "  - TXT reports: $((txt_count - raw_count))"
                echo -e "  - Raw text files: $raw_count"
            fi
        fi
    done
else
    echo -e "${RED}No test run directories found.${NC}"
fi

echo -e ""
echo -e "${GREEN}Implementation complete!${NC}"
echo -e "${BLUE}The system saved both DOCX and TXT versions of all reports and organized them by risk type.${NC}"
echo -e "${BLUE}The system attempted to use semantic retrieval with Pinecone but may have fallen back to mock analysis if API issues were encountered.${NC}"
echo -e ""
echo -e "${BLUE}Available flags:${NC}"
echo -e "  --force-embeddings   : Regenerate embeddings for the EU AI Act"
echo -e "  --skip-retrieval     : Skip semantic retrieval and use mock analysis"
echo -e ""
echo -e "${BLUE}Example usage:${NC}"
echo -e "  ./run_implementation.sh --force-embeddings"
echo -e "  ./run_implementation.sh --skip-retrieval" 
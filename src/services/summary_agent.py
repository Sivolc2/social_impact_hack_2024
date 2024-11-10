from typing import Dict, List
import logging
import anthropic
from anthropic import Anthropic
import os
import re

logger = logging.getLogger(__name__)

class SummaryAgent:
    def __init__(self):
        """Initialize the summary agent with Claude"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)
        
        # Load summary prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt for summary mode"""
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        try:
            with open(os.path.join(prompts_dir, "summary_prompt.txt"), "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading summary prompt: {str(e)}")
            raise

    async def create_summary_table(self, data_response: str) -> str:
        """Create a markdown table summarizing the data agent's response"""
        try:
            logger.debug(f"Creating summary table for response: {data_response[:100]}...")  # Log first 100 chars
            
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Create a summary table from this response:\n\n{data_response}"
                }]
            )
            
            response_text = message.content[0].text if message and message.content else ""
            logger.debug(f"Raw summary response: {response_text}")  # Log the raw response
            
            # Extract just the table if it exists
            table_match = re.search(r'(\|.*\|(\r?\n|$))+', response_text)
            if table_match:
                table_text = table_match.group(0)
                logger.debug(f"Extracted table: {table_text}")  # Log the extracted table
                return table_text
            else:
                logger.warning("No table found in summary response")
                return response_text
            
        except Exception as e:
            logger.error(f"Error creating summary table: {str(e)}")
            return "Error creating summary table"

    def format_html_table(self, markdown_table: str) -> str:
        """Convert markdown table to HTML table with styling"""
        logger.debug(f"Formatting table: {markdown_table}")  # Log the input markdown
        
        if not markdown_table or '|' not in markdown_table:
            logger.warning("No valid markdown table to format")
            return ""
            
        try:
            rows = markdown_table.strip().split('\n')
            html_rows = []
            
            for i, row in enumerate(rows):
                if '|-' in row:  # Skip markdown separator row
                    continue
                    
                cells = [cell.strip() for cell in row.split('|')[1:-1]]
                
                if i == 0:  # Header row
                    html_row = '<tr>' + ''.join(f'<th>{cell}</th>' for cell in cells) + '</tr>'
                else:  # Data rows
                    html_row = '<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>'
                html_rows.append(html_row)
            
            formatted_table = f"""
            <div class="summary-table">
                <table>
                    {''.join(html_rows)}
                </table>
            </div>
            """
            logger.debug(f"Formatted HTML table: {formatted_table}")  # Log the output HTML
            return formatted_table
            
        except Exception as e:
            logger.error(f"Error formatting HTML table: {str(e)}")
            return ""
        
# Reddit Scraper

A Python script to scrape top posts and their comments from a specified Reddit subreddit within a date range, clean the data, and export to an Excel file.

## Disclaimer

This tool is intended solely for educational and research purposes. Ensure full compliance with Reddit’s Terms of Service, Reddit API policies, and any applicable third-party platform usage rules. Always respect rate limits, authentication requirements, and community guidelines. Do not use this tool to scrape private, restricted, or user-protected content, and avoid any activity that could disrupt or overload Reddit’s services.

## Features

- Fetches top posts from a subreddit based on score.
- Retrieves all comments and replies recursively.
- Cleans and formats data into a unified structure.
- Outputs to Excel with columns for platform, subreddit, date, type, ID, description, and parent description.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/shikhar321/reddit-data-extraction-pipeline.git
   cd reddit-data-extraction-pipeline
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up Reddit API credentials:
   - Create a Reddit app at https://www.reddit.com/prefs/apps
   - Copy client_id, client_secret, and set a user_agent.
   - Create a `.env` file with:
     ```
     client_id=your_client_id
     client_secret=your_client_secret
     user_agent=your_user_agent
     ```

## Configuration

Edit `config.json` to set:
- `subreddit_name`: The subreddit to scrape (e.g., "royalenfield")
- `start_date` and `end_date`: Date range in YYYY-MM-DD format.
- `top_post_number`: Number of top posts to fetch.

## Usage

Run the script:
```
python main.py
```

## Final Output

The script produces one Excel file in the project directory:
   ```
{subreddit}_{startdate}_{enddate}.xlsx
   ```
Example:
   ```
royalenfield_20230101_20231231.xlsx
   ```
   
## Output Format

The Excel file contains the following columns:
- PLATFORM: Always "Reddit"
- ENTITY: Subreddit name
- DATE: Date in DD-MM-YYYY format
- TYPE: "POST", "COMMENT", or "REPLY"
- ID: Post or comment ID
- DESCRIPTION: Text content
- PARENT_DESCRIPTION: Parent post or comment text

## Dependencies

- praw: For Reddit API interaction
- pandas: For data manipulation
- python-dotenv: For loading environment variables
- openpyxl: For Excel output

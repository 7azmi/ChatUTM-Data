# WhatsApp Group Chat Processing

## Steps to Process Chat History

1. **Prepare Chat History**  
   - Export WhatsApp chat as `_chat.txt` in the proper group directory.

2. **Split Chat by Month**  
   - Run `split_chat.py`:  
     ```bash
     python split_chat.py
     ```  
   - Output: Monthly `.txt` files in `yyyy/mm.txt` structure.

3. **Convert to Markdown**  
   - Don't forget to add the OpenAI API key to `.env`:  
     ```
     OPENAI_API_KEY=your_api_key_here
     ```  
   - Run `convert_to_markdown.py`:  
     ```bash
     python convert_to_markdown.py
     ```  
   - Output: LLM-ready `.md` files in the same folder.

4. **Example Output**  
   ```markdown
   # Academic Group Summary

   ## Key Dates and Deadlines
   - **Next Semester Start Date**: 16 March 2025.
   - **Ramadan Study Mode**: Likely announced in March 2025.

   ## Course Registration Issues
   - **System Errors**: Issues with the new registration system.

   ## Recommended Professors
   - **OOP**: Dr. Luqman (good grades), Lizawati (fair grading).

   ## Exam Preparation
   - **Past Papers**: Shared for Database, Network Communication, etc.
from datetime import datetime
import time
import traceback



import os
import openai

import re


class OpenAITools:
    def __init__(self, api_key):            
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=self.api_key)
       



    def delete_assistants_by_name(self, assistant_name):        
        try:

            assistants = self.client.beta.assistants.list(
                order="desc",
                limit="100",
            )
            for assistant in assistants.data:
                print(assistant.name)


            # Filter assistants by name
            for assistant in assistants.data:
                if assistant.name == assistant_name:
                    # Hypothetical delete method (assuming API support)
                    print(f"Deleted assistant: {assistant.name} with ID: {assistant.id}")
                    response = self.client.beta.assistants.delete(assistant.id)
                    print(response)

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    #
    # Save all the assitants to disk
    #
    def snapshot_assistants(self):
        try:

            assistants = self.client.beta.assistants.list(
                order="desc",
                limit="100",
            )
            for assistant in assistants.data:
                print(assistant.name)
                # save assistent to a file 
                filename = "assistants/"+ assistant.name.replace(" ", "_") + ".md"
                # write to assistant.name as text
                with open(filename, 'w') as outfile:
                    outfile.write(assistant.instructions)
                    outfile.close() 

                    

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    def listModels(self):
        models = self.client.models.list()
        pattern = r"Model\(id='(.*?)', created=(\d+), object='(.*?)', owned_by='(.*?)'\)"
        output = re.findall(pattern, f'{models}')
        for model in output:
            model_id, created, object_type, owned_by = model
            print(f"Model ID: {model_id}, Created: {created}, Type: {object_type}, Owner: {owned_by}")


# Usage
if __name__ == "__main__":
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("No OPENAI_API_KEY environment variable set")
    
    assistant_id = "asst_sTkNITvBQnik6LuT2Sr6Rf6i"
    
    tools = OpenAITools(api_key)
   # tools.delete_assistants_by_name('Continue Agent')
    # tools.snapshot_assistants()
    tools.listModels()


  
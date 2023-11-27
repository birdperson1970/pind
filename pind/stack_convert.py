import json
import sys

def parse_trace_events(trace_events):
    execution_tree = None
    stack = []
    
    for event_dict in trace_events:
        if event_dict['event'] == 'call':
            frame = {
                "filename": event_dict['filename'],
                "function": event_dict['function'],
                "lineno": event_dict['lineno'],
                "children": [],
                "return_value": None,
                "local_vars": event_dict.get('local_vars', {}),
                "code_context": event_dict.get('code_context', '')
            }
            if stack:
                stack[-1]['children'].append(frame)
            else:
                execution_tree = frame
            stack.append(frame)
        elif event_dict['event'] == 'return':
            frame = stack.pop()
            frame['return_value'] = event_dict['return_value']
            if not stack:
                execution_tree = frame
        elif event_dict['event'] == 'line':
            stack[-1]['children'].append(event_dict)

    return execution_tree

def transform_trace_file(input_file_path, output_file_path):
    with open(input_file_path, 'r') as file:
        trace_data = json.load(file)  # Load the entire JSON array at once

    transformed_trace = parse_trace_events(trace_data)  # Transform the loaded trace events

    with open(output_file_path, 'w') as out_file:
        json.dump(transformed_trace, out_file, indent=2)

def main():
    if len(sys.argv) != 3:
        print("Usage: python stack_convert.py <input_file_path> <output_file_path>")
        sys.exit(1)

    input_trace_path = sys.argv[1]
    output_trace_path = sys.argv[2]
    transform_trace_file(input_trace_path, output_trace_path)
    print(f"Nested trace output saved to {output_trace_path}")

if __name__ == "__main__":
    main()

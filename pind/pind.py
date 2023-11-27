import datetime
import json
import os
import inspect
import io
import sys
import types

class Pind:
    def __init__(self, target_script, output_file=None):
        self.target_script = target_script
        self.target_script_absolute_path = os.path.abspath(target_script)
        self.output_file = output_file or self.generate_output_filename()
        # Ensure that the writer is opened only once and closed only once
        self.buffered_writer = io.open(self.output_file, 'w', buffering=1)
        self.tracing = True

    def generate_output_filename(self):
        # Create '.trace_dump' directory if it doesn't exist
        if not os.path.exists('.trace_dump'):
            os.makedirs('.trace_dump')

        # Create the directory '.trace_dump' if it doesn't exist
        output_dir = ".trace_dump"
        os.makedirs(output_dir, exist_ok=True)

        # Generate the filename for the trace output
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_wo_extension = os.path.splitext(os.path.basename(self.target_script))[0]
        return os.path.join(output_dir, f"{filename_wo_extension}_{timestamp}_trace.json")

    def trace_function(self, frame, event, arg):
        if self.tracing and event in ('call', 'line', 'return') and self.is_local_source(frame.f_code.co_filename):
            entry = self.serialize_frame(frame, event, arg)
            event_data = json.dumps(entry) + ',\n'
            self.buffered_writer.write(event_data)
        return self.trace_function




  
    def is_local_source(self, filename):
        if not filename.endswith('.py') or 'site-packages' in filename:
            return False
        
        # Get the absolute path of the target script's directory
        target_dir = os.path.dirname(self.target_script_absolute_path)
        # Normalize file paths for comparison
        filename = os.path.abspath(filename)
        target_dir = os.path.abspath(target_dir)

        # Check if the current file is a Python source file and is in the target directory
        return filename.endswith('.py') and os.path.commonpath([filename, target_dir]) == target_dir


    
    def serialize_frame(self, frame, event, arg):
        base_dir = os.path.dirname(os.path.abspath(self.target_script))
        absolute_frame_filename = os.path.abspath(frame.f_code.co_filename)
        relative_frame_filename = os.path.relpath(absolute_frame_filename, base_dir)

        frame_info = {
            "event": event,
            "filename": relative_frame_filename,
            "lineno": frame.f_lineno,
            "function": frame.f_code.co_name,
            "code_context": None,
            "local_vars": None if event != 'call' else self.serialize_locals(frame.f_locals),
            "return_value": None if event != 'return' else repr(arg)
        }

        try:
            lines, start_line = inspect.getsourcelines(frame)
            index = frame_info["lineno"] - start_line
            frame_info["code_context"] = lines[index].strip()
        except Exception as e:
            frame_info["code_context"] = str(e)

        return frame_info
    
    def stop(self):
        # This method should stop the tracing when called
        self.tracing = False  # Set the flag to indicate that tracing has ended
        sys.settrace(None)  # Remove the trace function
        self.buffered_writer.flush()  # Flush the remaining data in the buffer
        self.buffered_writer.close()  # Close the writer

    def __del__(self):
        # Ensure stop is called if __del__ is invoked
        self.stop()

    def serialize_locals(self, locals_dict):
        serialized_locals = {}
        for k, v in locals_dict.items():
            # Skip keys starting with "__" or in case of module/class objects
            if not k.startswith("__") and not isinstance(v, (type, types.ModuleType)):
                try:
                    serialized_locals[k] = repr(v)
                except Exception as e:
                    serialized_locals[k] = f"<object {type(v).__name__} could not be serialized: {e}>"
        return serialized_locals   


    def run(self):
        # Save the old system path
        old_sys_path = list(sys.path)
        script_dir = os.path.dirname(os.path.abspath(self.target_script))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        # ... rest of the run method ...
        with self.buffered_writer:
            self.buffered_writer.write('[')  # Start of the JSON list
            sys.settrace(self.trace_function)
            try:
                # Execute the target script
                with open(self.target_script) as f:
                    code = compile(f.read(), self.target_script, 'exec')
                    # Use only globals for proper resolution,
                    # which contains a reference to __main__ environment
                    exec(code, globals())
            finally:
                    sys.settrace(None)
                    sys.path = old_sys_path
                    self.buffered_writer.seek(self.buffered_writer.tell() - 2, io.SEEK_SET)  # Removing the last comma
                    self.buffered_writer.write('\n]')  # End of the JSON list


    def save_trace(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_wo_extension = os.path.splitext(os.path.basename(self.target_script))[0]
        trace_filename = f"{filename_wo_extension}_{timestamp}_trace.json"
        with open(trace_filename, 'w') as f:
            json.dump(self.trace_log, f, indent=2, sort_keys=True, default=str)
        return trace_filename
    
    def stop(self):
        # Ensure that stopping is idempotent
        if self.tracing:
            self.tracing = False
            sys.settrace(None)  # Remove the trace function
            
            # Only flush and close the buffered_writer if it's open
            if not self.buffered_writer.closed:
                self.buffered_writer.flush()
                self.buffered_writer.close()


    def __del__(self):
        self.stop()

# The entry point of the script execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ptrace.py script_to_trace.py")
        sys.exit(1)

    script_to_trace = sys.argv[1]
    
    # Create an instance of Pind with a given script
    tracer = Pind(script_to_trace)

    # Start the tracing process
    tracer.run()

    # There is no more trace log saving as it is streamed directly. Just printing the output file name.
    print(f"Trace output saved to {tracer.output_file}")

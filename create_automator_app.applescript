-- AppleScript to create Whisper Toggle Automator app
tell application "Automator"
	activate
	
	-- Create new application workflow
	set newWorkflow to make new workflow with properties {workflow type:application workflow}
	
	-- Add Run Shell Script action
	tell newWorkflow
		set shellAction to make new action with properties {name:"Run Shell Script"}
		tell shellAction
			set value of setting "inputMethod" to 0 -- as arguments
			set value of setting "shell" to "/bin/bash"
			set value of setting "script" to "cd /Users/saeed/Documents/GitHub/whisper
/usr/bin/python3 whisper_hotkey.py toggle"
		end tell
	end tell
	
	-- Save the workflow as an application
	save newWorkflow in file ((path to applications folder as string) & "Whisper Toggle.app")
	
	-- Close the workflow
	close newWorkflow
	
	display notification "Automator app created successfully!" with title "Whisper Setup"
	
end tell

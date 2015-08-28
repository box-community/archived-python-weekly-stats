# box-weekly-stats
Box Weekly User Report Script

This is a script that does an emailed weekly report on some basic usage statistics of Box across our domain at the University of Michigan.

The main script is box_data_archiver which is a shell script which emails the report and is set to run weekly at a specific time using Chron.  The script utilizes the Box APIs to access data for Box across our domain with the box.py module.  auth.conf and settings.conf are the configuration files used in running this script.  auth.conf is populated by running the box.py module and settings.conf needs parameters to be entered by the user of the script.  A spreadsheet in .csv form, with the date in the title, for all of the users across the domain is populated using fetch_user_data.py and then user_report.py crawls that data to crunch the numbers for the report.  We also add the shared accounts to a group just for shared accounts, to better administer them, using add_shared_to_group.py.  Lastly, we add a .tar.gz file of the .csv to a Box folder using upload_file.py.

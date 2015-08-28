# box-weekly-stats
Box Weekly User Report Script

This is a script that does an emailed weekly report on some basic usage statistics of Box across our domain at the University of Michigan.

The main script is box_data_archiver which is a shell script which emails the report and is set to run weekly at a specific time using Cron.  The script utilizes the Box APIs to access data for Box across our domain with the box.py module.  auth.conf and settings.conf are the configuration files used in running this script.  auth.conf is populated by running the box.py module and settings.conf needs parameters to be entered by the user of the script.  A spreadsheet in .csv form, with the date in the title, for all of the users across the domain is populated using fetch_user_data.py and then user_report.py crawls that data to crunch the numbers for the report.  We also add the shared accounts to a group just for shared accounts, to better administer them, using add_shared_to_group.py.  Lastly, we add a .tar.gz file of the .csv to a Box folder using upload_file.py.

Note that when our domain went to unlimited storage accounts for all our users, we added tracking codes for account_type and set the value to either "shared" or "admin".  The script is now based upon this configuration.  We had at one time hard-coded the allocation of space for different account types into the script, but our current solution is more readable and accurate in reporting.

Please see below for text of one of the reports that was sent out with the script.

-------

<b>Sample Email Report:</b><br>

Subject: Box User Report 2015-08-21

Summary for active user accounts<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total accounts: 49048<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total storage used: 91723.9 GB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mean storage used: 1.9 GB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Median storage used: 0.0 bytes<br>

Summary for active shared accounts<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total accounts: 845<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total storage used: 17754.5 GB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mean storage used: 21.0 GB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Median storage used: 240.3 MB<br>

Summary for active admin accounts<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total accounts: 11<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total storage used: 1.7 GB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mean storage used: 157.3 MB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Median storage used: 0.0 bytes<br>

Summary for inactive accounts<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total accounts: 3156<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total storage used: 2668.5 GB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mean storage used: 865.8 MB<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Median storage used: 0.0 bytes<br>

Summary for all accounts:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Top 1% of users account for: 12.45% of space used<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Top 10% of users account for: 30.49% of space used<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Top 25% of users account for: 47.84% of space used<br>

# Summary

- The only tool is used for this repo is Claude code
- Instructions for Running this project locally in `README.md`
- Each Claude code session has a corresponding entry in `session_logs/`
- There is a video demo in the description of the first PR https://github.com/taylor-chen/leads-tracker/pull/1 which contains the main body of work
- I kept a list of future features and areas we should revisit in https://github.com/taylor-chen/leads-tracker/issues


# Design decisions

## Prompting
- The functional and technical requirements i thought were complete enough for clade to setup a foundation for directory structure. I had a bunch of questions that I left inline via review comments in the PR that it opened in https://github.com/taylor-chen/leads-tracker/pull/1
- I suggested we use Postgres because i think there are potentially a lot of relationships in the data
- I did 2 separate sweeps one for security and one for code cleanup, if this were in a collaborative env, I would utilize skills and follow existing patterns where appropriate

## Data modelling
- The data model picked was for the simplicity, a Lead and an (internal attorney) User
- I thought this was acceptable because with the set of requirements, this is the most simple
- Thinking more long term, there might be a future need for a Lead to also create an account, in which case our data model would more likely look like:
  - Users: a user that can login to the system
  - Roles: which contains the title, initially lead, attorney
  - Permissions: sets what a role can do 
  - UserRoles: give a user a specific row

## Other Design considerations
- Currently we store uploaded files to the local storage, which is fine for local testing and a single server deployment, for production we would want to store uploaded files in blob storage
class AlumniSearch:
    search_fields = [
        'firstName', 'middleName', 'lastName', 'email',
        'existingEmail', 'approval__gsuite', 'membership__customer'
    ]

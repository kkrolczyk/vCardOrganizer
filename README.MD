#vCardOrganizer

Should:

        1. display partial implementation vcard
        2. allow to add and remove vcard from 'db'
        3. allow to search for a number/item (do we have it in db)
        4. allow to select particular vcards and export them to file.

Currently it's gui only, and probably will stay that way.  
Obviously multiple todos are scattered across the file.   
Uses vobject, http://vobject.skyhouseconsulting.com/ (Apache 2.0)
hovewer vobject does not support vCard 4.0 for now.
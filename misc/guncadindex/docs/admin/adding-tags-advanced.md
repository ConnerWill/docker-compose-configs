# Advanced Management of Tags and TaggingRules

**WARNING**: This is wicked overkill for most use cases. The tooling is mostly here so I can have a flat file to rapidly bootstrap new instances with.

## Why?

Defining tags and rules in a single file has its benefits:

* IaC. You can check this file into a repo and reduce the amount of configuration that exists as stateful data in your app
* Change control. You get this because, yaknow, IaC
* Easy definition of implication rules. You'll see

## Importing

If you have a YAML file and just want to import it, it's simple:

`./manage.py import-tagfile path-to-my.yml`

## Schema

Here's an example that showcases the schema of the yaml file you want to construct quite well:

Note that, while the data structures support tags with no category, **default-tags.yml does not**. Your tags should always have a category.

```yaml
---
somecategory:
  name: My Category # This is an external-facing name for the category
  description: This is my category # Also user-facing
  color: "#123456" # Optional, the color for all tags in this category
  tags: # The document should always have this as its topmost member
    example-tag: # This is an internal name for your tag. Use whatever
      name: My Tag # The user-facing name for your tag
      description: This is a super awesome tag # The description for your tag
      color: "#123abc" # Optionally, you can change its color. Defaults to boring white-on-grey
      lbry_tags: # Optionally, a list of LBRY tags can be defined here to catch releases that have them
        - fart
      rules: # Optionally, Tagging Rules can be defined here
        examplerule: # This is NOT an internal-only name and will show up in the DB
          title_regex: '^Barf$'
          description_regex: '^.*barf.*$'
          channel_regex: '^@barfman:b$'
          # Note: you can't use this field in this context. See further down
          #required_tag: barf
        anotherrule: # Multiple rules can be defined here
          title_regex: '^.*example.*$'
      # This is probably the single most powerful part of the yaml spec. By populating this
      # list, the importer tool will automatically construct TaggingRules with this tag as
      # the required and the implied tag as the applied one.
      # This means you could have a "Glock implies handgun" kind of relationship.
      # This relationship can nest. Glock 17 -> Glock -> Handgun
      implies: # Optional
        - foo
        - bar
        - 9mm
    another-tag:
      # ...
another-category:
  # ...
```

You should consult [`default-tags.yml`](/default-tags.yml) for further reference. If there's a feature in the YAML importer, it's because I wanted it for that file specifically.

## Caveats

* If you're using the `implies` field, you can only reference tags in the same file. They can be in other categories, though.

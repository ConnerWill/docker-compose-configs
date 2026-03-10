# 1.5.4

* Fixed: docker-compose now waits patiently for lbrynet to fully initialize
* Fixed: The seal in the About page is no longer incorrectly styled like the site icon
* Fixed: LBRY-only releases now actually show a LBRY button (fucking whoopsie)
* Fixed: Geoblocking now ignore /static and /media so we can serve styling in test mode
* Fixed: Pinned PG major version in docker-compose files
* Added: Age gate view now ensures it isn't cached and that all responses have valid CSRF cookies
* Added: Heavy restrictions for Cucks that aren't immediately blocked
* Added: Health check endpoint at /healthz

# 1.5.3

* Fixed: Erroneous tag ruules for WTFPL and Unlicense
* Added: Tag to filter by commercially-suitable licenses
* Added: A bunch of tests
* Added: A placeholder for EACH bookmark is now displayed on page load instead of just one
* Changed: Replaced a bunch of legacy CSS with equivalent SASS
* Changed: Moved old legacy CSS into SASS toolchain

# 1.5.2

* Added: Ability to enable/disable cucks and set validity dates
* Changed: App source now resides in its own directory in git instead of polluting the root dir

# 1.5.1

* Added: Tag for Auto Sear
* Added: django-cleanup to ensure we don't have unbounded image growth (oopie)

# 1.5.0

* Fixed: Removed debug prints for admin vote actions
* Fixed: Outbound URLs are redacted properly
* Fixed: API queries for releases with dots in their name now actually work (thanks siklikal)
* Fixed: Certain links in the footer are now hidden until you pass the age gate
* Fixed: Trigram searches are now an atomic transaction
* Fixed: S3 URLs aren't mangled for embeds
* Fixed: The blurb for not having any birthdays today now takes up the whole space the card would occupy, as expected
* Fixed: Thumbnail generation code now no longer reads back from storage and actually works
* Added: More caches are now cleared when votes are replied and reports are actioned
* Added: Metrics for visitor locale for visitors coming through Cloudflare
* Added: A place for you to view all of our partnered vendors
* Added: Tag for trinkets
* Added: Times are displayed in your local timezone if the CF-Timezone header is set
* Added: Geoblocking feature (see Cucks in admin dashboard)
* Added: Additional debugging information is now placed in the footer version string to match users to specific containers
* Added: Ability to look up individual releases in the API (thanks siklikal)
* Changed: Outbound clicks are now only tracked by domain, not full URL (sorry Prometheus)
* Changed: Post/update times on cards are now relative
* Changed: Vendor list now extends gracefully to two lines when necessary, centering overflow
* Changed: Disabled server-side cursors. This has a small but measurable performance impact, but allows for pgbouncer for resilience
* Changed: Disabled DB pooling. It offered few benefits and conflicts with pgbouncer
* Changed: Dockerfile now uses useradd instead of adduser
* Changed: Static assets are now baked into the image at build time. They are copied into `/data/static` if it exists for serving over reverse proxy
* Changed: Most DJDT toolbars are disabled in DEBUG
* Removed: Deprecated internal-only search form
* Removed: Some PROTIPs that no longer apply
* Removed: Cards no longer have a tooltip showing they are duplicates. Greying them out is fine
* Removed: Cards no longer show filesize, reducing clutter

# 1.4.4

* Added: Ability to serve media over S3
* Removed: Deprecated code for thumbnail juggling that did bad things with staticfiles

# 1.4.3

* Changed: Sponsors are now displayed more elegantly in the footer on mobile

# 1.4.2

* Fixed: Random debug logging statement in outbound view no longer echoes
* Fixed: Coverage script can no longer split-brain about debug being enabled
* Fixed: Outbound URLs are now tokenized to prevent forgery
* Added: Disclaimer page all users must accept before visiting
* Changed: Logo is now rasterized so it works on Tor again
* Changed: Minor verbiage alterations to disclaimer

# 1.4.1

* Added: Tag for eForms Ready -- add it to things that you know are in eForms and don't need to be manually entered
* Added: benchmark-search command for measuring search usability
* Added: Debug view for showing biased rank in Recently Updated
* Changed: Debugging commands now no longer impact code coverage results

# 1.4.0

* Updated: Django was upgraded to 6.0, a major version bump that gives us a lot more features
* Updated: Anything that depended on Django
* Fixed: Random bits of the header no longer find themselves in the body
* Fixed: DJDT isn't partially imported in prod envs
* Changed: Recently Updated is now more consistent and biases verified releases
* Changed: Reorganized the envvars in the deployment documentation to make more sense
* Added: Tag for S&W M&P series pistols
* Removed: Django-wiki. Information has been moved into a Mediawiki instance

# 1.3.4

* Added: Primitive download popularity tracking. Internal-only for right now, may become a public stat and factor into popularity calculations later
* Changed: Outbound link disclaimer handling is now more robust and does not require JS
* Changed: Wording on outbound link disclaimer and buttons were tightened
* Changed: Vendor links now use the outbound link filter

# 1.3.3

* Changed: Snowflakes are now only in the background and a lot less obnoxious

# 1.3.2

* Changed: Snow now falls for the whole month of December

# 1.3.1

* Fixed: Minor ordering warning with sitemaps
* Added: Test coverage for views
* Added: If images fail to load -- timeouts, 404s, etc. -- they try to display a placeholder
* Added: How many releases were added this month is now displayed above the search bar along with running totals
* Added: Date range filter for the last 3 months
* Changed: Image alt text is now hidden if images fail to load
* Removed: Old code for a federation feature that never happened

# 1.3.0

* Fixed: Search engines are now prevented from indexing outbound link pages
* Fixed: Some seriously fucked up dangling tags in the release detail view that really should've broken formatting a long time ago
* Added: The ability to bookmark releases. Bookmarks are displayed on the front page and can be bulk-cleared. Their use case is to let you browse around, find things you like, and then work through that stack of cool shit later
* Changed: Copy link to clipboard button is now on its own line
* Changed: Birthday/warning indicators in titles are now slapped onto the front, not the back where they can be truncated

# 1.2.4

* Fixed: All the primary color styling being completely wrong on the wiki
* Fixed: Styling for code blocks in descriptions
* Fixed: Help blurbs at the tops of posts are now correclty displayed (oops)
* Added: Outbound links now have you check off a disclaimer. This keeps us free from flak from Commiefornia
* Added: Documentation in README about legality, useful for self-hosters
* Removed: A line in the legalese document that could be construed as encouraging users to commit felonies

# 1.2.3

* Fixed: Historical migration that would throw warnings about timezone awareness
* Fixed: Traffic classifiers can now actually match empty strings
* Fixed: Banner messages on detail views with rails no longer take up the wrong grid area
* Added: Headers and inline code support for markdown
* Added: Testing for some admin data structures like navbar links and site banners
* Added: Some testing for the request classifier middleware
* Changed: Ensuring DB extensions are enabled is now done by overriding the migrate command, which works for test cases
* Changed: Traffic classifier rules are now always case-insensitive

# 1.2.2

* Fixed: Traffic classifier rules now have a method of matching empty strings
* Fixed: AI tagging command no longer gets orphaned during cronjob execution
* Fixed: Logging tons of bogus information to the cron console

# 1.2.1

* Fixed: Newlines in descriptions are now marked as line breaks
* Added: Support for nonstandard Lemmy search endpoints (required for some future plans)
* Added: Entry in robots.txt denying GPTBot
* Added: Tag for Glock 17L
* Added: Tag for muzzle devices in general
* Added: Tag for the Unlicense
* Added: Command for parsing through tag suggestions from gork
* Changed: Bots are now automatically filtered out of unique visitor metrics
* Changed: Traffic classifier rules can now have blank patterns to catch default cases
* Changed: Cronjob-related commands now use standard Python logging facilities
* Changed: Improve cronjob consistency, parallelize more tasks

# 1.2.0

* Fixed: Maintenance page now uses an older copy of legacy CSS for consistent formatting
* Fixed: Seasonal style overrides are now consistent between legacy CSS and SASS
* Fixed: Unnecessary JS console debug logging (like 2 lines on page load) was removed
* Added: On wide enough screens, related information will be displayed on a rail next to each release
* Added: Lemmy posts that mention a release will be displayed below it in the Detail view. Links leverage lemmyverse.link so you can point them all at your home instance with little fuss
* Added: Framework for obtaining stats on a release from Lemmy
* Changed: Similar releases is now truncated to 4 elements
* Changed: Release descriptions are now parsed for Markdown, enabling richer formatting
* Changed: Legacy CSS now defers to SASS for all variables
* Changed: Similarity manager will only update stats for up to 500 releases at a time to lower compute load
* Changed: Reworked some admin views on objects
* Changed: Revamp documentation
* Removed: LBRY stats are no longer shown on release detail pages, they're vastly inferior to other metrics of popularity
* Removed: Share buttons in favor of just showing Lemmy posts

# 1.1.18

* Fixed: Tag votes no longer throw a 500 upon submission

# 1.1.17

* Fixed: Sponsored vendor listings are no longer weirdly narrow on the wiki
* Fixed: Gitignore now also no longer ignores csv files
* Added: Releases can now be reported for various reasons
* Added: Admin UI for processing reports
* Changed: Order of sponsored vendors are now shuffled every few hours for fairness

# 1.1.16

* Fixed: Dockerignore now no longer ignores csv files

# 1.1.15

* Fixed: Starting commit for migration health checks is now fully disambiguated
* Fixed: Unlisted and abandoned releases now have the faux-button that says you can't view them on Odysee again
* Fixed: Share buttons don't get huge on unlisted releases
* Added: Release posts on Lemmy now have the Index logo on them
* Added: Fresh instances will now automatically import ~1.3k channels automatically on startup
* Changed: CONTRIBUTING.md was updated to reflect current code standards
* Removed: Old BLC channel list. It has served us well, but we need to move to a native replacement o7

# 1.1.14

* Added: CI now pushes update logs to Lemmy (hopefully)
* Added: Share links to other websites on detail view
* Added: Navbar links now dynamically wind up in the sitemap
* Removed: NAG22 tag as it causes huge false-positives with the AI

# 1.1.13

* Added: Modularized the navbar links so they can now be modified easily at runtime
* Added: The new release infrastructure can now collect stream claims from LBRY channels
* Changed: Tag vote processing screen got a facelift so it's actually usable on mobile
* Removed: Reddit links from About (o7 fosscad)

# 1.1.12

* Added: Grok's suggestions are now automatically added if a release was previously identified as wanting a tag that we didn't have
* Added: Tags for the Desert Eagle, its cartridges, and Magnum Research
* Added: Functionality for dynamically classifying traffic from Tor exit nodes
* Added: Modules to enforce database backward-compatibility to enable automatic blue-green deployment in the future
* Added: CI now has a database to work with (hopefully)

# 1.1.11

* Fixed: On account of me being silly, every request was doing a 10ms uncached DB call for no reason
* Added: A fifth recently updated release and the most unique thing this week
* Added: Tags for belt-feds
* Added: Tags for Taurus and their TX22
* Changed: Similarity stats for each release are now stored in the database and updating them is now outside the request path. This eliminates the latency from the highest-latency view by far, spreading that work out over time via a cronjob and lowering how much we keep in Valkey. Scraping traffic should now be significantly lighter on site infrastructure.
* Changed: Upgraded from psycopg2 to 3, which allows us to use connection pooling
* Changed: Minor wording change on timeframe sort options
* Changed: The way tags are presented in release cards is much more compact, more uniform, and now displays percentile metrics of uniqueness via coloration
* Changed: Release card thumbnails are now clamped to a 16:9 aspect ratio
* Changed: Release detail view thumbnails are also clamped to a 16:9 aspect ratio (this is incongruent with Odysee, just a heads up)

# 1.1.10

* Added: Silly easter egg if release count is between two numbers
* Added: 7.62x39mm tag
* Added: 15mm signaling flare tag
* Changed: Styling for vendor cards is a bit tighter on mobile
* Removed: No Description tag. It's outlived its purpose

# 1.1.9

* Fixed: Search suggestions that don't have thumbnails now show a placeholder image instead of just being broken
* Fixed: Failed thumbnail URL fetches now properly back off
* Added: Certain boolean columns in admin views are now appropriately marked up
* Added: Search suggestions now use placeholder colors for thumbnails
* Added: Pages in search engines will now have more detailed descriptions
* Changed: Thumbnail dominant colors are now double-checked via their cronjob. This fix mostly helps when dealing with test data
* Changed: Sitemap now contains all releases and caches more aggressively. Search engines will index the site a lot more effectively now
* Removed: Old deprecated default image that I didn't realize was still there

# 1.1.8

* Added: Date filtering (day/week/month/year/all time)
* Changed: Refactored some code to modularize it a bit

# 1.1.7

* Added: Thumbnails now have their dominant color associated with them, which is displayed while they load in
* Added: Releases that are LBRY-only now show the most popular repost that isn't, if one exists

# 1.1.6

* Added: Some initial DB setup in start.sh to fix bootstrapping new instances
* Added: Frontend support for channel filtering. Clicking channel names in detail and discover views now directs to a filtered search
* Added: Bones of SCSS support, some salvaged styling to be repaired later
* Changed: Legalese page now elaborates on how visitor stats are calculated
* Changed: Adjusted styling of the wiki, capping page width and hopefully making headers easier to parse
* Changed: Adjusted some DOM structure to add wrappers around images, preventing weird overflow situations
* Changed: Formatting for Atom feeds is now richer, exposing authors and tags as well as full item descriptions

# 1.1.5

* Fixed: Referer traffic classification rules now work again
* Added: Pulled in a library for more robust bot detection based on UA strings
* Added: Tag for Mossberg
* Added: Tag for .32 ACP and Skorp

# 1.1.4

* Fixed: Typos that really, really shouldn't have wound up in prod

# 1.1.3

* Fixed: Marked some fields as safe in templates since they contain no UGC
* Added: Referer metrics
* Added: Quality of life functions for the admin panel

# 1.1.2

* Fixed: Added some sanity checks when downloading thumbnails

# 1.1.1

* Fixed: Encountering an error while validating the results of a bulk claim search now doesn't stop the rest of the search from processing
* Fixed: Error handler code in AI tagging algo now returns a tuple, as should be expected

# 1.1.0

* Fixed: Deletion of OdyseeRelease objects no longer causes weird failures when attempting to clear caches
* Added: Section on the Discover page that shows releases with high uniqueness scores
* Added: More licenses
* Added: Mechanism for the LLM to suggest tag additions
* Added: M1911 and Colt tags (how did we not have these yet)
* Added: Airgun tag to disambiguate from airsoft guns
* Added: We now calculate how unique a release is based on how popular their tags are and allow users to sort by this new metric. Should hopefully make it easier to find hidden gems
* Added: Docker Compose that pulls from the registry
* Changed: Hybrid, Frame, and Printed Firearm tags have been replaced by a much more granular set of tags
* Changed: Minor tweaks to advanced search form
* Changed: Overhauled the Discover view (by which I mean rotated so everything actually lines up)
* Changed: Front page now shows the most unique from this month

# 1.0.9

* Changed: Fundamentally revise the visitor metrics a second time
* Changed: Reduced minimum size of description box to reclaim some space
* Changed: Simplified repost stats in detail view since they're no longer relevant to popularity weighting

# 1.0.8

* Added: Better cache handling when models are altered
* Changed: Visitor hash is now salted with the Django secret
* Changed: Visitor count metrics now roll instead of being cleanly separated per-day
* Changed: Presentation of footer elements has been polished, icons in buttons are now all the same size

# 1.0.7

* Added: Anonymous unique visitor count metrics per day, week, and month

# 1.0.6

* Added: Ability to filter by channel via the API. Use ?channel=@handle:a. No UI just yet

# 1.0.5

* Fixed: Another occurrence (and a really bad one at that) of improper cache usage causing additional latency for no reason
* Fixed: Related releases no longer prefetch a ton of data leading to huge latency spikes for no reason
* Fixed: Release cards no longer have an erroneous second tab selection point at their titles
* Added: Thumbnails in detail view for authors' channels
* Added: Thumbnails in autocomplete listings
* Added: Thumbnails to API. Please be considerate and do not embed them -- request and cache them yourself
* Added: Tooltips on hover for releases. Tooltips contain untruncated titles
* Changed: License text is now clamped to prevent overspill
* Changed: Tags on detail views are now displayed on their own line and below download buttons on mobile
* Removed: Duplicated sort options

# 1.0.4

* Fixed: Caching now works on the front page
* Added: CI bot configuration to gitlab-ci
* Added: Caching for channel thumbnails on Discover
* Added: Caching on the FAQ page
* Added: Admin tools for managing the cache
* Changed: Recently Updated now only shows the latest change from each channel, to prevent bulk uploads from clogging it up
* Changed: Maintenance page has been buffed

# 1.0.3

* Added: More stats in the license-stats utility
* Changed: Tiny CSS tweaks to reduce content reflows on page load
* Changed: Scrolling background is now a GIF, improving page performance

# 1.0.2

* Fixed: Advanced Search layout being too narrow on most devices
* Fixed: Thumbnails on mobile now properly expand to the width of the device in detail views
* Added: Another cool propaganda poster by PLINK
* Added: Support for animated thumbnails
* Added: Tags for licenses
* Changed: Max tags shown on each release card increased by 2
* Changed: Release and Channel thumbnails have been moved to a better management system and will be periodically refreshed
* Removed: Defunct instances of old Index logos
* Removed: Animations that caused content reflows. They were flashy but not helpful
* Removed: Some bunk code in classification middleware

# 1.0.1

* Fixed: Incongruent fonts in search bar
* Fixed: Styling reflow with footer buttons on mobile
* Fixed: Styling errors with sitewide banners on mobile
* Fixed: Button in tag vote page is now centered again
* Fixed: Minor styling inconsistency with footer
* Fixed: Bins for popularity are wider
* Fixed: AI tagging now works again (again)
* Added: Admin controls when viewing releases
* Added: Flamethrower tag
* Added: TaggingRule stats in the admin UI
* Added: If a line in a description contains just a tag's name or slug, it's added
* Added: More modular, simpler, more maintainable Release infrastructure
* Added: Some holiday easter eggs
* Changed: Some comments in the head are now removed

# 1.0.0

The big one-oh-oh.

Major features in this release:
* A gigantic visual facelift that makes better use of space and is generally just more cohesive. And darker
* The search bar now gives suggestions, letting you navigate instantly to a release if you know what you're after
* Changes to search sort/display options take effect immediately now
* We track Odysee's views, likes, and dislikes, leveraging them for more accurate popularity calculations and improving search results
* If you make a typo, we now offer the closest correction we can find. This is homebrew and might be a bit off sometimes -- let me know if you encounter weirdness
* Voluntary channel discovery has been simplified to posting one release with guncad as a tag

List of all changes:
* Fixed: Long titles on mobile no longer result in overflow in detail views
* Fixed: Certain stale caches are now proactively cleared when invalidated
* Fixed: An occurrence or two of the old logo
* Fixed: Entries in the Tag Vote handler view are more consistently sorted
* Added: Proper user account controls to the main site UI (that most of you will never see)
* Added: We can now super unverify things by flagging them as dangerous if we REALLY need to
* Added: We now have the ability to set up site-wide banners
* Added: OpenSearch.xml stuff (hopefully correctly)
* Added: Channel discovery now only requires you to tag a RELEASE with guncad, not your channel
* Added: (JS) Changes to Format/Sort now take effect immediately
* Added: Search autocompletion
* Added: Search correction (it's not perfect, don't hate me if it's off a bit)
* Added: We now tightly control trigram thresholds
* Added: We now track Odysee metadata, including views, likes, dislikes, etc.
* Changed: Duplicate releases now inherit the release state of their parent, since the criteria are only for the file, not the listing
* Changed: Tag overflow is now represented by its own pseudo-tag-lookin-thing
* Changed: Site is now darker, scrolling background image had contrast lowered to compensate
* Changed: Gigantic visual overhaul
* Changed: We now no longer acquire releases if they're unlisted the first time we see them
* Changed: Having Grok hit releases it's already tagged is now locked behind a flag
* Changed: We now use the popularity ranking factor in place of LBC amount when sorting in a few places
* Changed: Views and likes, when available, boost placement in search rankings
* Removed: Extraneous admin view that shows all tags, since that's now in Advanced Search
* Removed: Images are no longer indexed, which should prevent a lot of grifter ads in the future
* Removed: Some erroneous, outdated PROTIPs

# 0.13.3

* Fixed: Renaming tags no longer causes dupe key violations
* Fixed: Using the wrong favicons in a couple places
* Added: New tags for S&W SD/SW series pistols
* Changed: The Ruger P90 tag has been retooled into Ruger P Series

# 0.13.2

* Fixed: We're now 50% as scrutinizing when looking for new channels
* Fixed: Bootstrapping the Index no longer dies due to incorrect perms in the lbrynet container
* Fixed: The trigram extension is added automatically
* Added: Bitcoin donation link
* Added: DMCA verbiage (lbrynet obeys Odysee's blacklist)
* Added: Moderation features for channels
* Added: The time each channel was added is now tracked
* Added: guncadindex is now a shibboleth tag
* Changed: Animated background now has lower contrast, should help with the nausea-prone among us
* Changed: Logo has been revised and is now based on a vector image and automatically generated

# 0.13.1

* Fixed: AI can now tag releases again

# 0.13.0

* Fixed: Certain files in the Dockerfile are now properly marked as executable
* Added: Trigram searching. Substring searches now work, as do certain mild typos
* Added: New categories for traffic classification: referrer header and request path
* Added: Indices for some common Release fields
* Added: Claims with the "noindex" tag will, as expected, not be indexed. This extends to both channels and releases
* Added: The detail view of a release now shows 3 related releases. It's not perfect, but it's cool for exploration
* Changed: Sponsors (of which we've taken none) now have their order in the footer shuffled for fairness
* Changed: Grid view is now the default
* Changed: The popularity of a particular release is now stored in the DB for faster lookups

# 0.12.11

* Fixed: Certain files that should've been removed during container build time are now gone
* Fixed: Certain Prometheus metrics erroneously counted invisible releases
* Fixed: Traffic classifier rules are now sorted properly in the admin UI
* Added: Metrics exposing distribution of release count, bucketed by channel
* Added: Metrics exposing the popularity factor of releases on the Index
* Changed: Metrics for repost count per release have had their bins narrowed
* Changed: Metrics worker now resides in the "metrics" app
* Changed: There's now a 1-second backoff before restarting the metrics worker
* Changed: We're now much less lenient about file permissions in builds
* Removed: Releases per channel metric (way too high cardinality)
* Removed: Dupe ratio metric (it can be derived from other info too easily)

# 0.12.10

* Added: System for dynamically classifying requests for use in metrics
* Added: Metrics app, request metrics
* Changed: We now only automatically restart Gunicorn while in debug mode

# 0.12.9

* Changed: Gunicorn recycles workers slowly again, move Prometheus metric collection to its own separate worker process, fixing a memory leak (hopefully)

# 0.12.8

* Changed: Gunicorn now recycles workers a lot faster

# 0.12.7

* Fixed: Releases now properly override the release state of their parent channel
* Fixed: Releases now embed their large thumbnails in OG meta, which are more suitable for the type of Twitter cards we now use
* Fixed: #138 Wrapped thumbnails are the width of their containers again
* Fixed: Descriptions of releases use simpler template syntax
* Fixed: Titles on Discover page no longer break wrapping
* Added: We now track the support amount in addition to the effective amount
* Changed: The popularity algorithm now has a much higher weight for community-contributed LBC than author-contributed LBC. This will dramatically impact search results sorted by popularity
* Changed: Verified releases are now weighted more highly in search rankings
* Changed: Search algorithm is now more modular, and the popularity sort has been altered to sort by it
* Changed: We now only use summary_large_image twitter cards for direct links to releases

# 0.12.6

* Fixed: Discovered channels are no longer imported with legacy handles
* Fixed: Add signal to substitute and fix legacy handles for channels

# 0.12.5

* Added: Twitter meta tags
* Added: Schema.org metadata

# 0.12.4

* Fixed: Onion middleware now sets cookie security properly

# 0.12.3

* Fixed: Last update dates will no longer change if the release hasn't actually come out yet
* Fixed: LBRY URLs no longer fail due to browsers thinking they're links to low ports
* Fixed: Typo in seal description (fuck)
* Added: Ability to toggle off tracking updates (in case of spam)
* Added: Documentation on dependencies

# 0.12.2

* Fixed: Release state on OdyseeRelease objects is now blankable

# 0.12.1

* Fixed: Thumbnails on mobile are now as wide as they were before
* Fixed: Minor scrolling bug on certain screen sizes
* Fixed: Sizes measured in just bytes no longer show decimals
* Fixed: Feeds sorted by updates now properly only show updates
* Added: Seal is now shown on detail view
* Added: Bulk administration tools for verifying releases
* Changed: Unified the look of release cards between mobile and grid view
* Changed: Seal size is now slightly smaller

# 0.12.0

Major features in this release:
* We now have a wiki! Right now it documents the Index and a few th ings auxiliary to it, but it will expand in time. Editorship is invite-only for right now.
* We now have an official seal of approval! The requirements are documented on the "About" page, but if you see that seal, you can have a good expectation that the release will be certifiably not-garbage. Thanks cringelemon for the art <3
* Advanced searching has been implemented. Right now, it's just tag filtering, but there'll be more to come in the future.
* Related to the above: we now have really for real tag filtering. They still match up in text searches, of course
* You can now get an Atom feed for any search query
* The backbone of onion link support has been added -- it's all infrastructure shit now

List of all changes:
* Fixed: The landing view, when it doesn't have a birthday, no longer offsets recently-updated releases to the left on desktop
* Fixed: Discover view now actually knows what day it is
* Fixed: Thumbnails in grid views are now always the same height
* Added: Whether a release is a duplicate or not is now visible via the API
* Added: Framework for showcasing the quality of releases (thanks @cringelemon for graphic design work)
* Added: Real, proper tag filtering. Works in the API, too
* Added: Advanced search form, to be filled out with more options as time goes on
* Added: Foundational work for onion links
* Added: System for showing when releases can only be viewed on LBRY Desktop
* Added: AI model for tagging can now be configured on-the-fly
* Added: Wiki is now displayed publicly in the navbar
* Added: Atom feed support for any search query
* Added: Finally customized styling on the Rest API page
* Added: Documented a bunch of models and fields
* Added: Framework for taking sponsored vendors
* Changed: We're now a bit more strict about showing birthdays

# 0.11.5

* Fixed: Missing styling on some admin tools
* Fixed: OpenGraph Metadata now shows up and is consumed properly when you link to the Index again
* Added: If a release has more than 7 tags, the list gets truncated in grid/list views
* Added: Vulnerability scanning
* Added: We now update the base OS image, just to be safe
* Changed: GitLab CI now uses the same build methods as GunCAD Mirror for parity
* Changed: Formatting for Wiki. Like a lot.

# 0.11.4

* Fixed: Wiki formatting

# 0.11.3

* Fixed: Discover page now caches to Redis to make page loads faster
* Added: A wiki, to be furnished with information in due time

# 0.11.2

* Added: AI autotagging batch size is now configurable at runtime

# 0.11.1

* Fixed: The "updated" sort now actually sorts out only updated objects, like it was supposed to

# 0.11.0

* Fixed: The repost discoverer now works again (oops)
* Added: The "ai-tag" command, which tags the n most recent releases it hasn't seen yet with tags. Prod will be hooked up to Grok
* Added: Tons more tagging rules
* Added: Expanded discovery rules slightly to account for common "shibboleth" tags (like "guncad")
* Added: Tag count pseudo-histogram metric to prometheus endpoint
* Added: Moderators can now see (but not edit) more information about releases in the admin UI

# 0.10.16

* Fixed: Birthdays are now consistently referred to (as Birthdays, dammit)
* Fixed: Birthdays no longer kick over at a timezone-unlocalized time
* Fixed: Releases in grid view now take up all the space they're allocated
* Added: Birthdays now have little cakes in places to show that they're birthdays
* Added: A small amount of framework for adding trusted vendor support
* Added: Support for scouring ALL of LBRY for GunCAD channels
* Changed: Only one birthday is now shown on the front page, with more room for recents
* Changed: Abandoned claims no longer show download links, seeing as how they're useless

# 0.10.15

* Added: GunCAD Index Prometheus metrics, publicly available at /metrics

# 0.10.14

* Fixed: Abandoned claims are no longer considered for a bunch of things

# 0.10.13

* Added: We now display any anniversaries/birthdays on the front page. Order is governed by a seeded random function.
* Changed: Minor differences in how we track abandoned claims now mean we can offer more useful stats on them
* Changed: Last update date is now tracked using the sha384sum of the stream, not the more volatile sdhash

# 0.10.12

* Added: We now track when each file was last updated
* Fixed: The gunicorn recovery thing now actually works

# 0.10.11

* Added: We now keep track of the last-seen sdhash and expose it via the API

# 0.10.10

* Fixed: Division by zero error in dev during certain pages of queries
* Fixed: Hanging quotes in queries no longer cause HTTP 500 errors
* Fixed: Gunicorn automatically restarts in the container now
* Changed: `import-tagfile` now uses tag slugs, which means cross-file compat is now possible
* Changed: "About" was put back into the navbar since we have space again
* Changed: Admin links in the navbar are now denoted as yellow

# 0.10.9

* Fixed: Images in footer now have proper alt text
* Changed: Tags are now bigger and easier to read

# 0.10.8

* Fixed: UberClay's secret feature thing now actually works okay

# 0.10.7

* Added: Secret feature for UberClay

# 0.10.6

* Added: Support for statsd exporting was added, see admin docs for details
* Added: We now serve fonts directly, which should result in much faster page render times
* Added: CI now lints YAML files
* Added: There's now a separate "Legal" page, accessible in the footer. It doesn't have anything new, I just split it from "About"
* Changed: The "About" page has been overhauled
* Changed: We no longer depend on FontAwesome, replacing it for Heroicons since it's friendlier and lighter

# 0.10.5

* Added: URLs are now slugs based on the shortest unambiguous LBRY URL instead of claim ID
* Added: Releases now have a button to copy their URLs to the clipboard
* Fixed: "noon" and "midnight" are now no longer displayed in time fields
* Changed: Maintenance page is now a bit more helpful
* Changed: Various pages on mobile are now much tighter than before, making the viewing experience more dense
* Changed: Front page now displays the 4 most recent releases, as that seems to be more helpful

# 0.10.4

* Fixed: Minor spelling mistake
* Added: We now have proper icons for when authors/releases are missing thumbnails
* Added: Blurb in the footer should help with SEO
* Added: Titles now have suffixes, main page now shows the site tagline in its title
* Added: Tags for Steyr AUG
* Changed: About link was moved to the footer
* Changed: OG Metadata is now improved all across the website
* Changed: Tags are now more muted in color. Idea here is to draw focus toward the thumbnail more than the tags.

# 0.10.3

* Added: Image scraper job now has a unique User-Agent string
* Changed: Footer was redone along with a small section of the main page

# 0.10.2

* Added: robots.txt and sitemap.xml support
* Added: Anti-nausea mode (disables background). This feature requires JS to set & lookup cookies

# 0.10.1

Hotfix
* Fixed: Dockerignore was ignoring staticfiles(!!!)

# 0.10.0

Major features in this release:
* Major performance improvements(?!) across the board, especially at the API
* API calls can now search the Index the exact same way as any other user
* Shortlinks we create will now be displayed on pages for items that have them
* Shortlinks are now case insensitive and thus easier to type
* Duplicate releases are now detected and will direct users to the (hopefully) original/most popular source of the file
* If your channel is Indexed and you repost (/boost/whatever) another channel, we pick up on it. Boost cool people so we can find em
* You can now add GunCAD Index to your phone as an app

List of all changes:
* Added: We now look at reposts of authors we know for potential new authors
* Added: Backend support for basic tag filtering via the `?tag=ar-15` or whatever queries. Frontend UI support to come later
* Added: Releases are now deduplicated, with dupes being displayed grayed-out
* Added: Links to shortlinks are now displayed next to releases
* Added: Put indexes in place for release date, improving search speed
* Added: Debugging instances now display the Django Debug Toolbar plugin for extra... debugging, I guess
* Added: SQL calls in the landing page are now significantly faster due to caching (~50%)
* Added: Search page results are now ~50% quicker to return from the DB
* Added: API access for everything is now SIGNIFICANTLY faster
* Added: API can now use the same search and sort parameters as the main search page
* Fixed: Deprecated symbols in LBRY resource URLs are replaced with undeprecated ones
* Fixed: Metadata for old releases is now updated in the Index when those releases change
* Fixed: Cleaned up some tech debt with regard to filtering out unindexed content
* Fixed: Sitewide static files are now stored in an appropriately sitewide directory
* Fixed: Grid view now uses smaller thumbnails for more efficient loading and data transfer
* Fixed: Shortlinks are now case-insensitive
* Removed: Internal logic that yielded redundantly long handles for channels

# 0.9.2

* Added: Progressive Webapp (PWA) support

# 0.9.1

* Fixed: Several places that were erroneously using/showing hidden/disabled content have been fixed
* Changed: Footer has been redesigned for (what feels like) better presentation
* Changed: We now hide claims that are completely unsupported and cannot be recovered. You may notice ~20 or so releases removed from the Index as a result -- there was no way to ever get ahold of them.
* Changed: Improved heuristics for discovering new channels based on existing data

# 0.9.0

* Changed: Split into three containers, each handling a different process

# 0.8.2

* Added: Tags for laser aiming modules

# 0.8.1

* Changed: References to AWCY? now clarify that they are deindexed

# 0.8.0

Major features in this release:
* There's now a grid view, and it's the default if you hit the "Browse" button
* There's now a "Discover" page which shuffles daily
* We now autodiscover channels if they have `guncad` in the title (and meet a couple other criteria)

List of all changes:
* Added: Channels are now automatically detected if they have `guncad` or similar tags in their description and meet some basic criteria
* Added: A brand new "Discover" tab, with content shuffled nightly
* Added: A new grid view for organizing search results and browsing
* Added: Channels can now be excluded from automatic updates
* Added: The detail view of a release now shows all of its metadata
* Fixed: Erroneous release dates are now clamped to the time the claim was made
* Fixed: Scrape job now retrieves claim IDs for channels that don't have them separately, fixing a chicken-and-egg problem

# 0.7.4

* Added: Shortlink support (@Alyosha3DPrintFreedom)

# 0.7.3

* Fixed: We no longer discard ~10% of all information acquired from LBRY concerning releases (oops) (@YoungBreezy)

# 0.7.2

* Added: Default tag rules for Ruger SD9(s)
* Added: Tags for pistol braces, disambiguating them from Stocks, and bipods

# 0.7.1

* Added: Significant optimizations to channel scraping now mean it completes incredibly quickly.
* Fixed: Handles for channels are now indexed properly

# 0.7.0

* Added: Users can now vote for tags, which are approved/denied by website administrators
* Added: Tags now have categories, which determine their color and grouping in other portions of the website
* Added: Tons and tons and TONS of new tagging rules

# 0.6.3

* Added: Rules for TEC-9s
* Added: sha384sums of files are now displayed beneath them and exposed via the API
* Added: We now scrape Odysee channels for up-to-date names and backend data
* Added: We now get thumbnails for channels
* Added: Timestamps now include exact time

# 0.6.2

* Fixed: Popular widget on the front page no longer shows future releases

# 0.6.1

* Fixed: Let admins search for releases by ID
* Fixed: Removed a random debugging statement

# 0.6.0

Major features in this release:
* Tagging has been significantly overhauled -- voting for tags is now right on the horizon
* Polling rate is now much faster -- there's at most a 1h delay in seeing something on the Index
* Lots of UI fixes

List of all changes:
* Fixed: Odysee link on details page needed a space and didn't have it
* Fixed: LBRY links are now available via the API
* Fixed: (Low-level thing) LBRY links are now urlencoded at the template and not at the model
* Fixed: (Low-level thing) Some important static assets now need to be collected before Gunicorn starts
* Added: There's now backend support for manual tag adding/blacklisting, overriding any automatic tagging done!
* Added: TONS of new tagging rules
* Added: Releases now have LBRY tags in their descriptions
* Added: Linked to 3D Gun Builder's getting started guide in the "About" page
* Changed: Mobile users no longer see alternate download links (since they probably don't want them anyway)
* Changed: Polling rate is now much higher, since we can afford it. There is now, at worst, a 1h delta between posting things to Odysee and seeing them here

# 0.5.0

* Fixed: Started keeping a changelog
* Added: Added Fontawesome 6 and put glyphs in appropriate places
* Added: You now get a "Back" button when you click a release from the search view, but not when visiting a direct link from someone else
* Added: Detail view now has a link to LBRY Desktop, for those who have it installed
* Added: Rules for s3igu2's Leber
* Added: Rules for Hoffman's SL-15
* Changed: Tags are now slightly fatter
* Changed: Background now scrolls on mobile like it does on desktop
* Changed: Service now queries a local LBRY instance instead of reaching out to Odysee -- scraping is now much faster

# 0.4.1

* Added: Tagging rules for Wafflemags

# 0.4.0

* Initial release

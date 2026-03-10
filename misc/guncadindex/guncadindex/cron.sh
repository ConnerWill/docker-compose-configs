#! /bin/bash
# GunCAD Index cronjob script
# Notably absent: set -e
# We want this script to continue if a cronjob fails for whatever reason

manage="python3 manage.py"

# Django-native stuff
$manage clearsessions &		# Removes stale sessions from the store

# Independent scripts that can fork immediately
$manage cache-tor-exit-nodes &	# Minor thing, used for stat collection. Completes fast and shouldn't block anything
$manage odysee-stats \
	--update-first-page \
	--all-null \
	--pace 0.3 \
	--batch-size 50 \
	& # Hit Odysee's API for metadata
$manage process-suggestions &	# Process Grok's tag suggestions
$manage update-uniqueness &	# Calculate uniqueness metrics (pretty cheap)
$manage update-lemmy &		# Update cached Lemmy-related data (takes time, but isn't that heavy)

# Wait for LBRY to become ready before we do LBRY-native jobs
$manage wait-for-wallet &	# Wait until LBRY's ready, case it's bouncing

# Wait here
# This'll let the previous tasks wrap up along with the wait-for-wallet task
# This lets wait-for-wallet go stale, mind, but that's not what we're trying
# to prevent with it.
wait

# LBRY shit
$manage discover &		# Look for new channels
$manage scrape &		# Scrape for content

# Wait for us to have that content before we act on it
wait

$manage release-update-thumbnails & # Update all thumbnails
(
$manage tag			# Tag that content
# With tags in place, we can ask Grok to supplement them
if [ -n "$GUNCAD_AI_XAI_API_KEY" ]; then
	$manage ai-tag --batch-size "${GUNCAD_AI_BATCH_SIZE:-100}" # Tag with Grok, if that's a tool we have
fi
) &
$manage deduplicate &		# Deduplicate it
$manage update-similar &	# Update similarity statistics (can be VERY expensive)

# Wait for all tasks to wrap up
wait

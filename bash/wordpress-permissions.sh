#!/bin/bash

set -o nounset

ADMINUSER="root"
ADMINGROUP="blogadmin"
WEBSERVERUSER="apache"
#WEBSERVERUSER="www-data"
BLOGS=$(ls /srv/blog/)

U=$ADMINUSER
G=$ADMINGROUP
W=$WEBSERVERUSER

# Users & Groups used:  
#     "adm" for files/dirs that should only be writable by an admin.
#     "apache" for those that need to be writable by the web server.

# Where user:group is root:adm, the files must be publically readable so the web server running as the apache user can access them.

# Permissions
for p in $BLOGS; do
    if [[ $p == "" ]]; then
        echo "Error: p is unset!"
        continue
    fi
    if [[ $p == "/" ]]; then
        echo "Um, no."
        continue
    fi
    echo "$p"
    # Set permissions. While Wordpress guidelines say 755 for dirs and 644 for files, we control access with the group as well so 775 and 664 are more appropriate.
    find "$p" -type d -exec chmod 775 {} \;
    find "$p" -type f -exec chmod 664 {} \;

    # wp-config.php
    chmod 664 "$p"/wp-config.php

    # Set default user:group ownership, by default adminuser and admingroup
    chown -R "$U":"$G" "$p"

    # /
    # The root WordPress directory: all files should be writable only by your user account, except .htaccess if you want WordPress to automatically generate rewrite rules for you.
    chown "$U":"$G" "$p"
    chown "$U":"$G" "$p"/*

    # /wp-admin
    # The WordPress administration area: all files should be writable only by your user account.
    chown -R "$U":"$G" "$p"/wp-admin

    # /wp-content/
    # User-supplied content: intended to be completely writable by all users (owner/user, group, and public).
    MYDIR="$p"/wp-content
    chown "$U":"$W" "$MYDIR"
    chown "$U":"$W" "$MYDIR"/*
    find "$MYDIR" -type d -exec chmod 777 {} \;
    find "$MYDIR" -type f -exec chmod 666 {} \;

    # /wp-content/themes/
    # Theme files. If you want to use the built-in theme editor, all files need to be group writable. If you do not want to use the built-in theme editor, all files can be writable only by your user account.
    MYDIR="$p"/wp-content/themes
    chown -R "$U":"$G" "$MYDIR"
    find "$MYDIR" -type d -exec chmod 775 {} \;
    find "$MYDIR" -type f -exec chmod 664 {} \;

    # /wp-content/plugins/
    # Plugin files: all files should be writable only by your user account.
    MYDIR="$p"/wp-content/plugins
    chown -R "$U":"$G" "$MYDIR"
    find "$MYDIR" -type d -exec chmod 775 {} \;
    find "$MYDIR" -type f -exec chmod 664 {} \;
done

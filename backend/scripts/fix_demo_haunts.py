#!/usr/bin/env python
"""
Fix demo haunt configurations with better selectors that actually work.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'watcher.settings')
django.setup()

from apps.haunts.models import Haunt

def fix_nodejs_releases():
    """Fix Node.js Releases haunt"""
    haunt = Haunt.objects.filter(name='Node.js Releases').first()
    if not haunt:
        print("✗ Node.js Releases haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "latest_lts_version": {
                "operator": "changed"
            }
        },
        "selectors": {
            "latest_lts_version": "table tbody tr:first-child td:first-child",
            "latest_current_version": "table tbody tr td:first-child"
        },
        "normalization": {
            "latest_lts_version": {
                "type": "text",
                "strip": True
            },
            "latest_current_version": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_react_docs():
    """Fix React Documentation haunt"""
    haunt = Haunt.objects.filter(name='React Documentation').first()
    if not haunt:
        print("✗ React Documentation haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "latest_blog_post": {
                "operator": "changed"
            }
        },
        "selectors": {
            "latest_blog_post": "main h1",
            "page_title": "title"
        },
        "normalization": {
            "latest_blog_post": {
                "type": "text",
                "strip": True
            },
            "page_title": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_python_releases():
    """Fix Python Release Notes haunt"""
    haunt = Haunt.objects.filter(name='Python Release Notes').first()
    if not haunt:
        print("✗ Python Release Notes haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "latest_version": {
                "operator": "changed"
            }
        },
        "selectors": {
            "latest_version": ".download-list-widget li:first-child a",
            "release_date": ".download-list-widget li:first-child p"
        },
        "normalization": {
            "latest_version": {
                "type": "text",
                "strip": True
            },
            "release_date": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_hacker_news():
    """Fix Hacker News Top Story haunt"""
    haunt = Haunt.objects.filter(name='Hacker News Top Story').first()
    if not haunt:
        print("✗ Hacker News Top Story haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "top_story": {
                "operator": "changed"
            }
        },
        "selectors": {
            "top_story": ".athing:first-child .titleline > a",
            "top_story_points": ".athing:first-child + tr .score"
        },
        "normalization": {
            "top_story": {
                "type": "text",
                "strip": True
            },
            "top_story_points": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_paul_graham():
    """Fix Paul Graham Essays haunt"""
    haunt = Haunt.objects.filter(name='Paul Graham Essays').first()
    if not haunt:
        print("✗ Paul Graham Essays haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "latest_essay": {
                "operator": "changed"
            }
        },
        "selectors": {
            "latest_essay": "table font a:first-of-type",
            "essay_count": "table font a"
        },
        "normalization": {
            "latest_essay": {
                "type": "text",
                "strip": True
            },
            "essay_count": {
                "type": "count"
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_sam_altman():
    """Fix Sam Altman Blog haunt"""
    haunt = Haunt.objects.filter(name='Sam Altman Blog').first()
    if not haunt:
        print("✗ Sam Altman Blog haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "latest_post": {
                "operator": "changed"
            }
        },
        "selectors": {
            "latest_post": "article:first-of-type h2 a, .post:first-of-type h2 a",
            "latest_post_date": "article:first-of-type time, .post:first-of-type .date"
        },
        "normalization": {
            "latest_post": {
                "type": "text",
                "strip": True
            },
            "latest_post_date": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_mastercard_scholars():
    """Fix Mastercard Foundation Scholars haunt"""
    haunt = Haunt.objects.filter(name='Mastercard Foundation Scholars').first()
    if not haunt:
        print("✗ Mastercard Foundation Scholars haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "application_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "application_status": "h1, .page-title",
            "deadline_info": "main p:contains('deadline'), main p:contains('application')"
        },
        "normalization": {
            "application_status": {
                "type": "text",
                "strip": True
            },
            "deadline_info": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_icann_fellowship():
    """Fix ICANN Fellowship Program haunts"""
    haunts = Haunt.objects.filter(name='ICANN Fellowship Program')
    if not haunts.exists():
        print("✗ ICANN Fellowship Program haunt not found")
        return
    
    for haunt in haunts:
        haunt.config = {
            "alert_on": {
                "program_status": {
                    "operator": "changed"
                }
            },
            "selectors": {
                "program_status": "h1, .page-title",
                "application_info": "main p:first-of-type"
            },
            "normalization": {
                "program_status": {
                    "type": "text",
                    "strip": True
                },
                "application_info": {
                    "type": "text",
                    "strip": True
                }
            }
        }
        haunt.save()
    print(f"✓ Fixed {haunts.count()} ICANN Fellowship Program haunt(s)")

def fix_mozilla_fellowships():
    """Fix Mozilla Fellowships haunt"""
    haunt = Haunt.objects.filter(name='Mozilla Fellowships').first()
    if not haunt:
        print("✗ Mozilla Fellowships haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "fellowship_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "fellowship_status": "h1, main h2:first-of-type",
            "application_info": "main p:first-of-type"
        },
        "normalization": {
            "fellowship_status": {
                "type": "text",
                "strip": True
            },
            "application_info": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_gsoc_timeline():
    """Fix Google Summer of Code Timeline haunt"""
    haunt = Haunt.objects.filter(name='Google Summer of Code Timeline').first()
    if not haunt:
        print("✗ Google Summer of Code Timeline haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "next_milestone": {
                "operator": "changed"
            }
        },
        "selectors": {
            "next_milestone": "table tr:first-child td:first-child, .timeline-item:first-of-type h3",
            "milestone_date": "table tr:first-child td:last-child, .timeline-item:first-of-type .date"
        },
        "normalization": {
            "next_milestone": {
                "type": "text",
                "strip": True
            },
            "milestone_date": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_mlh_fellowship():
    """Fix MLH Fellowship - Open Source haunt"""
    haunt = Haunt.objects.filter(name='MLH Fellowship - Open Source').first()
    if not haunt:
        print("✗ MLH Fellowship - Open Source haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "application_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "application_status": "h1, main h2:first-of-type",
            "program_info": "main p:first-of-type"
        },
        "normalization": {
            "application_status": {
                "type": "text",
                "strip": True
            },
            "program_info": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_yc_batch():
    """Fix YC Batch Announcements haunt"""
    haunt = Haunt.objects.filter(name='YC Batch Announcements').first()
    if not haunt:
        print("✗ YC Batch Announcements haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "latest_announcement": {
                "operator": "changed"
            }
        },
        "selectors": {
            "latest_announcement": "article:first-of-type h3 a, .post:first-of-type h2 a",
            "announcement_date": "article:first-of-type time, .post:first-of-type .date"
        },
        "normalization": {
            "latest_announcement": {
                "type": "text",
                "strip": True
            },
            "announcement_date": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_aws_health():
    """Fix AWS Service Health haunt"""
    haunt = Haunt.objects.filter(name='AWS Service Health').first()
    if not haunt:
        print("✗ AWS Service Health haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "service_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "service_status": ".status-indicator, #status",
            "latest_issue": ".issue:first-of-type h3, .event:first-of-type"
        },
        "normalization": {
            "service_status": {
                "type": "text",
                "strip": True
            },
            "latest_issue": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_heroku_status():
    """Fix Heroku Status haunt"""
    haunt = Haunt.objects.filter(name='Heroku Status').first()
    if not haunt:
        print("✗ Heroku Status haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "incident_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "incident_status": ".page-status .status, .status-indicator",
            "latest_incident": ".incident-title:first-of-type, .unresolved-incident:first-of-type .incident-title"
        },
        "normalization": {
            "incident_status": {
                "type": "text",
                "strip": True
            },
            "latest_incident": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_github_status():
    """Fix GitHub Status haunt"""
    haunt = Haunt.objects.filter(name='GitHub Status').first()
    if not haunt:
        print("✗ GitHub Status haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "system_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "system_status": ".page-status .status, .status-indicator",
            "latest_incident": ".incident-title:first-of-type"
        },
        "normalization": {
            "system_status": {
                "type": "text",
                "strip": True
            },
            "latest_incident": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_devcon_mauritius():
    """Fix Devcon Mauritius haunt"""
    haunt = Haunt.objects.filter(name='Devcon Mauritius').first()
    if not haunt:
        print("✗ Devcon Mauritius haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "conference_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "conference_status": "h1, .page-title",
            "registration_info": "main p:contains('registration'), main p:contains('ticket')"
        },
        "normalization": {
            "conference_status": {
                "type": "text",
                "strip": True
            },
            "registration_info": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_pycon_us():
    """Fix PyCon US 2026 haunt"""
    haunt = Haunt.objects.filter(name='PyCon US 2026').first()
    if not haunt:
        print("✗ PyCon US 2026 haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "conference_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "conference_status": "h1, .page-title",
            "important_dates": "main p:contains('date'), .dates"
        },
        "normalization": {
            "conference_status": {
                "type": "text",
                "strip": True
            },
            "important_dates": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_aws_reinvent():
    """Fix AWS re:Invent Conference haunt"""
    haunt = Haunt.objects.filter(name='AWS re:Invent Conference').first()
    if not haunt:
        print("✗ AWS re:Invent Conference haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "registration_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "registration_status": "h1, .hero-title",
            "event_dates": "main p:contains('date'), .event-date"
        },
        "normalization": {
            "registration_status": {
                "type": "text",
                "strip": True
            },
            "event_dates": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

def fix_miles_morland():
    """Fix Miles Morland Foundation haunts"""
    haunts = Haunt.objects.filter(name__icontains='Miles Morland') | Haunt.objects.filter(name='mmf')
    if not haunts.exists():
        print("✗ Miles Morland Foundation haunt not found")
        return
    
    for haunt in haunts:
        haunt.config = {
            "alert_on": {
                "application_status": {
                    "operator": "changed"
                }
            },
            "selectors": {
                "application_status": "h1, .page-title",
                "entry_requirements": "main p:first-of-type, .requirements"
            },
            "normalization": {
                "application_status": {
                    "type": "text",
                    "strip": True
                },
                "entry_requirements": {
                    "type": "text",
                    "strip": True
                }
            }
        }
        haunt.save()
    print(f"✓ Fixed {haunts.count()} Miles Morland Foundation haunt(s)")

def fix_edinburgh_mastercard():
    """Fix University of Edinburgh - Mastercard Foundation Scholars haunt"""
    haunt = Haunt.objects.filter(name='University of Edinburgh - Mastercard Foundation Scholars').first()
    if not haunt:
        print("✗ University of Edinburgh - Mastercard Foundation Scholars haunt not found")
        return
    
    haunt.config = {
        "alert_on": {
            "application_status": {
                "operator": "changed"
            }
        },
        "selectors": {
            "application_status": "h1, .page-title",
            "scholarship_info": "main p:first-of-type"
        },
        "normalization": {
            "application_status": {
                "type": "text",
                "strip": True
            },
            "scholarship_info": {
                "type": "text",
                "strip": True
            }
        }
    }
    haunt.save()
    print(f"✓ Fixed {haunt.name}")

if __name__ == '__main__':
    print("=" * 60)
    print("Fixing all demo haunt configurations...")
    print("=" * 60)
    
    # Tech/Development
    fix_nodejs_releases()
    fix_react_docs()
    fix_python_releases()
    fix_hacker_news()
    fix_paul_graham()
    fix_sam_altman()
    
    # Fellowships & Scholarships
    fix_mastercard_scholars()
    fix_icann_fellowship()
    fix_mozilla_fellowships()
    fix_mlh_fellowship()
    fix_miles_morland()
    fix_edinburgh_mastercard()
    
    # Programs & Opportunities
    fix_gsoc_timeline()
    fix_yc_batch()
    
    # Service Status
    fix_aws_health()
    fix_heroku_status()
    fix_github_status()
    
    # Conferences
    fix_devcon_mauritius()
    fix_pycon_us()
    fix_aws_reinvent()
    
    print("=" * 60)
    print("✓ All haunts fixed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Go to the frontend UI")
    print("2. Click the refresh button (↻) on each haunt")
    print("3. Wait for the scrape to complete")
    print("4. You should now see meaningful alerts!")
    print("=" * 60)

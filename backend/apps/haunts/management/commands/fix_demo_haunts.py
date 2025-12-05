from django.core.management.base import BaseCommand
from apps.haunts.models import Haunt


class Command(BaseCommand):
    help = 'Fix demo haunt configurations with better selectors'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Fixing all demo haunt configurations...")
        self.stdout.write("=" * 60)
        
        # Tech/Development
        self.fix_nodejs_releases()
        self.fix_react_docs()
        self.fix_python_releases()
        self.fix_hacker_news()
        self.fix_paul_graham()
        self.fix_sam_altman()
        
        # Fellowships & Scholarships
        self.fix_mastercard_scholars()
        self.fix_icann_fellowship()
        self.fix_mozilla_fellowships()
        self.fix_mlh_fellowship()
        self.fix_miles_morland()
        self.fix_edinburgh_mastercard()
        
        # Programs & Opportunities
        self.fix_gsoc_timeline()
        self.fix_yc_batch()
        
        # Service Status
        self.fix_aws_health()
        self.fix_heroku_status()
        self.fix_github_status()
        
        # Conferences
        self.fix_devcon_mauritius()
        self.fix_pycon_us()
        self.fix_aws_reinvent()
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✓ All haunts fixed!"))
        self.stdout.write("=" * 60)
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Go to the frontend UI")
        self.stdout.write("2. Click the refresh button (↻) on each haunt")
        self.stdout.write("3. Wait for the scrape to complete")
        self.stdout.write("4. You should now see meaningful alerts!")
        self.stdout.write("=" * 60)

    def fix_nodejs_releases(self):
        haunt = Haunt.objects.filter(name='Node.js Releases').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Node.js Releases haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"latest_lts_version": {"operator": "changed"}},
            "selectors": {
                "latest_lts_version": "table tbody tr:first-child td:first-child",
                "latest_current_version": "table tbody tr td:first-child"
            },
            "normalization": {
                "latest_lts_version": {"type": "text", "strip": True},
                "latest_current_version": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_react_docs(self):
        haunt = Haunt.objects.filter(name='React Documentation').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ React Documentation haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"latest_blog_post": {"operator": "changed"}},
            "selectors": {
                "latest_blog_post": "main h1",
                "page_title": "title"
            },
            "normalization": {
                "latest_blog_post": {"type": "text", "strip": True},
                "page_title": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_python_releases(self):
        haunt = Haunt.objects.filter(name='Python Release Notes').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Python Release Notes haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"latest_version": {"operator": "changed"}},
            "selectors": {
                "latest_version": ".download-list-widget li:first-child a",
                "release_date": ".download-list-widget li:first-child p"
            },
            "normalization": {
                "latest_version": {"type": "text", "strip": True},
                "release_date": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_hacker_news(self):
        haunt = Haunt.objects.filter(name='Hacker News Top Story').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Hacker News Top Story haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"top_story": {"operator": "changed"}},
            "selectors": {
                "top_story": ".athing:first-child .titleline > a",
                "top_story_points": ".athing:first-child + tr .score"
            },
            "normalization": {
                "top_story": {"type": "text", "strip": True},
                "top_story_points": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_paul_graham(self):
        haunt = Haunt.objects.filter(name='Paul Graham Essays').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Paul Graham Essays haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"latest_essay": {"operator": "changed"}},
            "selectors": {
                "latest_essay": "table font a:first-of-type",
                "essay_count": "table font a"
            },
            "normalization": {
                "latest_essay": {"type": "text", "strip": True},
                "essay_count": {"type": "count"}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_sam_altman(self):
        haunt = Haunt.objects.filter(name='Sam Altman Blog').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Sam Altman Blog haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"latest_post": {"operator": "changed"}},
            "selectors": {
                "latest_post": "article:first-of-type h2 a, .post:first-of-type h2 a",
                "latest_post_date": "article:first-of-type time, .post:first-of-type .date"
            },
            "normalization": {
                "latest_post": {"type": "text", "strip": True},
                "latest_post_date": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_mastercard_scholars(self):
        haunt = Haunt.objects.filter(name='Mastercard Foundation Scholars').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Mastercard Foundation Scholars haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"application_status": {"operator": "changed"}},
            "selectors": {
                "application_status": "h1, .page-title",
                "deadline_info": "main p:first-of-type"
            },
            "normalization": {
                "application_status": {"type": "text", "strip": True},
                "deadline_info": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_icann_fellowship(self):
        haunts = Haunt.objects.filter(name='ICANN Fellowship Program')
        if not haunts.exists():
            self.stdout.write(self.style.WARNING("✗ ICANN Fellowship Program haunt not found"))
            return
        
        for haunt in haunts:
            haunt.config = {
                "alert_on": {"program_status": {"operator": "changed"}},
                "selectors": {
                    "program_status": "h1, .page-title",
                    "application_info": "main p:first-of-type"
                },
                "normalization": {
                    "program_status": {"type": "text", "strip": True},
                    "application_info": {"type": "text", "strip": True}
                }
            }
            haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunts.count()} ICANN Fellowship Program haunt(s)"))

    def fix_mozilla_fellowships(self):
        haunt = Haunt.objects.filter(name='Mozilla Fellowships').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Mozilla Fellowships haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"fellowship_status": {"operator": "changed"}},
            "selectors": {
                "fellowship_status": "h1, main h2:first-of-type",
                "application_info": "main p:first-of-type"
            },
            "normalization": {
                "fellowship_status": {"type": "text", "strip": True},
                "application_info": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_gsoc_timeline(self):
        haunt = Haunt.objects.filter(name='Google Summer of Code Timeline').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Google Summer of Code Timeline haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"next_milestone": {"operator": "changed"}},
            "selectors": {
                "next_milestone": "table tr:first-child td:first-child, .timeline-item:first-of-type h3",
                "milestone_date": "table tr:first-child td:last-child, .timeline-item:first-of-type .date"
            },
            "normalization": {
                "next_milestone": {"type": "text", "strip": True},
                "milestone_date": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_mlh_fellowship(self):
        haunt = Haunt.objects.filter(name='MLH Fellowship - Open Source').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ MLH Fellowship - Open Source haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"application_status": {"operator": "changed"}},
            "selectors": {
                "application_status": "h1, main h2:first-of-type",
                "program_info": "main p:first-of-type"
            },
            "normalization": {
                "application_status": {"type": "text", "strip": True},
                "program_info": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_yc_batch(self):
        haunt = Haunt.objects.filter(name='YC Batch Announcements').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ YC Batch Announcements haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"latest_announcement": {"operator": "changed"}},
            "selectors": {
                "latest_announcement": "article:first-of-type h3 a, .post:first-of-type h2 a",
                "announcement_date": "article:first-of-type time, .post:first-of-type .date"
            },
            "normalization": {
                "latest_announcement": {"type": "text", "strip": True},
                "announcement_date": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_aws_health(self):
        haunt = Haunt.objects.filter(name='AWS Service Health').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ AWS Service Health haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"service_status": {"operator": "changed"}},
            "selectors": {
                "service_status": ".status-indicator, #status",
                "latest_issue": ".issue:first-of-type h3, .event:first-of-type"
            },
            "normalization": {
                "service_status": {"type": "text", "strip": True},
                "latest_issue": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_heroku_status(self):
        haunt = Haunt.objects.filter(name='Heroku Status').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Heroku Status haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"incident_status": {"operator": "changed"}},
            "selectors": {
                "incident_status": ".page-status .status, .status-indicator",
                "latest_incident": ".incident-title:first-of-type, .unresolved-incident:first-of-type .incident-title"
            },
            "normalization": {
                "incident_status": {"type": "text", "strip": True},
                "latest_incident": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_github_status(self):
        haunt = Haunt.objects.filter(name='GitHub Status').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ GitHub Status haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"system_status": {"operator": "changed"}},
            "selectors": {
                "system_status": ".page-status .status, .status-indicator",
                "latest_incident": ".incident-title:first-of-type"
            },
            "normalization": {
                "system_status": {"type": "text", "strip": True},
                "latest_incident": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_devcon_mauritius(self):
        haunt = Haunt.objects.filter(name='Devcon Mauritius').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ Devcon Mauritius haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"conference_status": {"operator": "changed"}},
            "selectors": {
                "conference_status": "h1, .page-title",
                "registration_info": "main p:first-of-type"
            },
            "normalization": {
                "conference_status": {"type": "text", "strip": True},
                "registration_info": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_pycon_us(self):
        haunt = Haunt.objects.filter(name='PyCon US 2026').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ PyCon US 2026 haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"conference_status": {"operator": "changed"}},
            "selectors": {
                "conference_status": "h1, .page-title",
                "important_dates": "main p:first-of-type"
            },
            "normalization": {
                "conference_status": {"type": "text", "strip": True},
                "important_dates": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_aws_reinvent(self):
        haunt = Haunt.objects.filter(name='AWS re:Invent Conference').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ AWS re:Invent Conference haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"registration_status": {"operator": "changed"}},
            "selectors": {
                "registration_status": "h1, .hero-title",
                "event_dates": "main p:first-of-type"
            },
            "normalization": {
                "registration_status": {"type": "text", "strip": True},
                "event_dates": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

    def fix_miles_morland(self):
        haunts = Haunt.objects.filter(name__icontains='Miles Morland') | Haunt.objects.filter(name='mmf')
        if not haunts.exists():
            self.stdout.write(self.style.WARNING("✗ Miles Morland Foundation haunt not found"))
            return
        
        for haunt in haunts:
            haunt.config = {
                "alert_on": {"application_status": {"operator": "changed"}},
                "selectors": {
                    "application_status": "h1, .page-title",
                    "entry_requirements": "main p:first-of-type, .requirements"
                },
                "normalization": {
                    "application_status": {"type": "text", "strip": True},
                    "entry_requirements": {"type": "text", "strip": True}
                }
            }
            haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunts.count()} Miles Morland Foundation haunt(s)"))

    def fix_edinburgh_mastercard(self):
        haunt = Haunt.objects.filter(name='University of Edinburgh - Mastercard Foundation Scholars').first()
        if not haunt:
            self.stdout.write(self.style.WARNING("✗ University of Edinburgh - Mastercard Foundation Scholars haunt not found"))
            return
        
        haunt.config = {
            "alert_on": {"application_status": {"operator": "changed"}},
            "selectors": {
                "application_status": "h1, .page-title",
                "scholarship_info": "main p:first-of-type"
            },
            "normalization": {
                "application_status": {"type": "text", "strip": True},
                "scholarship_info": {"type": "text", "strip": True}
            }
        }
        haunt.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Fixed {haunt.name}"))

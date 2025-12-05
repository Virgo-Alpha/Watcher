"""
Management command to populate demo data for testing and demonstrations.
Creates a demo user with folders, private haunts, and subscribes to public haunts.
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.haunts.models import Haunt, Folder
from apps.subscriptions.models import Subscription
from apps.ai.services import AIConfigService

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate database with demo data for testing and demonstrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='demo@watcher.local',
            help='Email for demo user (default: demo@watcher.local)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='demo123',
            help='Password for demo user (default: demo123)',
        )
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Delete existing demo data and recreate',
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        recreate = options['recreate']
        
        # Get or create demo user
        demo_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'is_active': True,
            }
        )
        
        if created:
            demo_user.set_password(password)
            demo_user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created demo user: {email} / {password}')
            )
        else:
            if recreate:
                # Delete existing data
                Haunt.objects.filter(owner=demo_user).delete()
                Folder.objects.filter(user=demo_user).delete()
                self.stdout.write(
                    self.style.WARNING(f'Deleted existing data for {email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Demo user already exists: {email}')
                )
        
        # Define folder structure
        folders_data = [
            {'name': 'Work', 'parent': None},
            {'name': 'Opportunities', 'parent': None},
            {'name': 'Personal', 'parent': None},
            {'name': 'News & Tech', 'parent': None},
        ]

        # Define demo haunts - reliable, public sites with clear change signals
        # Using manual configs instead of AI to ensure reliability
        demo_haunts = [
            # Work folder - Service status pages
            {
                'name': 'GitHub Status',
                'url': 'https://www.githubstatus.com/',
                'description': 'Monitor GitHub service status - is everything operational?',
                'folder': 'Work',
                'scrape_interval': 15,
                'use_manual_config': True,
            },
            {
                'name': 'Heroku Status',
                'url': 'https://status.heroku.com/',
                'description': 'Check Heroku platform status for any incidents',
                'folder': 'Work',
                'scrape_interval': 30,
                'use_manual_config': False,  # Let AI handle this one
            },
            {
                'name': 'AWS Service Health',
                'url': 'https://health.aws.amazon.com/health/status',
                'description': 'Monitor AWS service health dashboard for any service disruptions',
                'folder': 'Work',
                'scrape_interval': 30,
                'use_manual_config': True,
            },

            # Opportunities folder - Fellowship/scholarship/program applications
            {
                'name': 'YC Batch Announcements',
                'url': 'https://www.ycombinator.com/blog/tag/admissions',
                'description': 'Monitor Y Combinator for new batch application announcements',
                'folder': 'Opportunities',
                'scrape_interval': 1440,
                'use_manual_config': False,
            },
            {
                'name': 'MLH Fellowship - Open Source',
                'url': 'https://fellowship.mlh.io/programs/open-source',
                'description': 'Check if MLH Fellowship applications are open for the next cohort',
                'folder': 'Opportunities',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
            {
                'name': 'Google Summer of Code Timeline',
                'url': 'https://developers.google.com/open-source/gsoc/timeline',
                'description': 'Monitor GSoC timeline for application period dates and deadlines',
                'folder': 'Opportunities',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
            {
                'name': 'Mozilla Fellowships',
                'url': 'https://www.mozillafoundation.org/en/what-we-do/fellowships/',
                'description': 'Check if Mozilla Fellowship nominations are open',
                'folder': 'Opportunities',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
            {
                'name': 'ICANN Fellowship Program',
                'url': 'https://www.icann.org/fellowshipprogram',
                'description': 'Monitor ICANN Fellowship application status and deadlines',
                'folder': 'Opportunities',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
            {
                'name': 'Mastercard Foundation Scholars',
                'url': 'https://global.ed.ac.uk/mastercard-foundation-scholars-program/apply-for-a-scholarship',
                'description': 'Check if Mastercard Foundation scholarship applications are open',
                'folder': 'Opportunities',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },

            # Personal folder - Blogs and personal interest
            {
                'name': 'Sam Altman Blog',
                'url': 'https://blog.samaltman.com/',
                'description': 'Monitor for new blog posts from Sam Altman',
                'folder': 'Personal',
                'scrape_interval': 1440,
                'use_manual_config': False,
            },
            {
                'name': 'Paul Graham Essays',
                'url': 'http://www.paulgraham.com/articles.html',
                'description': 'Check for new essays from Paul Graham',
                'folder': 'Personal',
                'scrape_interval': 1440,
                'use_manual_config': False,
            },

            # News & Tech folder - Tech news and releases
            {
                'name': 'Hacker News Top Story',
                'url': 'https://news.ycombinator.com/',
                'description': 'Track the top story on Hacker News',
                'folder': 'News & Tech',
                'scrape_interval': 60,
                'use_manual_config': False,
            },
            {
                'name': 'Python Release Notes',
                'url': 'https://www.python.org/downloads/',
                'description': 'Check for new Python version releases and security updates',
                'folder': 'News & Tech',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
            {
                'name': 'React Documentation',
                'url': 'https://react.dev/',
                'description': 'Monitor React docs for version updates and major announcements',
                'folder': 'News & Tech',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
            {
                'name': 'Node.js Releases',
                'url': 'https://nodejs.org/en/about/previous-releases',
                'description': 'Monitor Node.js for new LTS and current releases',
                'folder': 'News & Tech',
                'scrape_interval': 1440,
                'use_manual_config': True,
            },
        ]
        
        ai_service = AIConfigService()
        folders_created = {}
        
        # Manual configs for haunts that need specific selectors
        manual_configs = self._get_manual_configs()
        
        with transaction.atomic():
            # Create folders
            for folder_data in folders_data:
                folder, created = Folder.objects.get_or_create(
                    name=folder_data['name'],
                    user=demo_user,
                    defaults={'parent': None}
                )
                folders_created[folder_data['name']] = folder
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created folder: {folder.name}')
                    )
            
            # Create haunts
            created_count = 0
            for haunt_data in demo_haunts:
                folder_name = haunt_data.pop('folder', None)
                use_manual = haunt_data.pop('use_manual_config', False)
                folder = folders_created.get(folder_name) if folder_name else None
                
                self.stdout.write(f'Processing: {haunt_data["name"]}...')
                
                # Use manual config if specified, otherwise try AI
                if use_manual and haunt_data['name'] in manual_configs:
                    config = manual_configs[haunt_data['name']]
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Using manual config'))
                else:
                    # Generate AI configuration
                    try:
                        config = ai_service.generate_config(
                            url=haunt_data['url'],
                            description=haunt_data['description']
                        )
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Generated AI config'))
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed to generate config: {str(e)}')
                        )
                        # Use fallback config
                        config = {
                            'selectors': {
                                'content': 'body',
                            },
                            'normalization': {},
                            'truthy_values': {},
                        }
                        self.stdout.write(self.style.WARNING(f'  ⚠ Using fallback config'))
                
                # Create haunt
                haunt, created = Haunt.objects.get_or_create(
                    name=haunt_data['name'],
                    owner=demo_user,
                    defaults={
                        'url': haunt_data['url'],
                        'description': haunt_data['description'],
                        'config': config,
                        'folder': folder,
                        'is_public': False,
                        'scrape_interval': haunt_data['scrape_interval'],
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created haunt: {haunt.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Haunt already exists: {haunt.name}')
                    )
        
        # Subscribe to all public haunts
        self.stdout.write('\nSubscribing to public haunts...')
        public_haunts = Haunt.objects.filter(is_public=True).exclude(owner=demo_user)
        subscribed_count = 0
        
        for public_haunt in public_haunts:
            subscription, created = Subscription.objects.get_or_create(
                user=demo_user,
                haunt=public_haunt,
                defaults={'notifications_enabled': True}
            )
            if created:
                subscribed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Subscribed to: {public_haunt.name} (by {public_haunt.owner.email})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Completed!'
                f'\n  • Created {created_count} personal haunts'
                f'\n  • Organized into {len(folders_created)} folders'
                f'\n  • Subscribed to {subscribed_count} public haunts'
                f'\n  • Demo credentials: {email} / {password}'
            )
        )

    def _get_manual_configs(self):
        """Return manual configurations for haunts that need specific selectors."""
        return {
            'GitHub Status': {
                'selectors': {
                    'overall_status': '[data-component-id="page_status"]',
                    'status_description': '.page-status span',
                    'incident_count': '.unresolved-incidents .font-largest',
                },
                'normalization': {
                    'overall_status': {
                        'type': 'attribute',
                        'attribute': 'data-status',
                        'transform': 'lowercase',
                    },
                    'status_description': {
                        'type': 'text',
                        'strip': True,
                    },
                    'incident_count': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'overall_status': {
                        'operator': 'not_equals',
                        'value': 'operational'
                    }
                }
            },
            'AWS Service Health': {
                'selectors': {
                    'healthy_services': 'div[data-testid="service-health-card"] span:contains("Service is operating normally")',
                    'degraded_services': 'div[data-testid="service-health-card"]:has(span:contains("degraded"))',
                    'status_summary': 'h1.awsui-util-f-s',
                },
                'normalization': {
                    'healthy_services': {
                        'type': 'count',
                    },
                    'degraded_services': {
                        'type': 'count',
                    },
                    'status_summary': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'degraded_services': {
                        'operator': 'greater_than',
                        'value': 0
                    }
                }
            },
            'Google Summer of Code Timeline': {
                'selectors': {
                    'application_period': 'table.timeline-table tr:contains("Potential GSoC contributors discuss") td:last-child',
                    'org_announcement': 'table.timeline-table tr:contains("Organization Announcement") td:last-child',
                    'coding_period': 'table.timeline-table tr:contains("Coding officially begins") td:last-child',
                },
                'normalization': {
                    'application_period': {
                        'type': 'text',
                        'strip': True,
                    },
                    'org_announcement': {
                        'type': 'text',
                        'strip': True,
                    },
                    'coding_period': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'application_period': {
                        'operator': 'changed',
                    }
                }
            },
            'Node.js Releases': {
                'selectors': {
                    'current_version': 'a[href*="/download/current/"] strong',
                    'lts_version': 'a[href*="/download/"] strong:contains("LTS")',
                    'latest_release_date': 'table.download-matrix tbody tr:first-child td:nth-child(3)',
                },
                'normalization': {
                    'current_version': {
                        'type': 'text',
                        'strip': True,
                    },
                    'lts_version': {
                        'type': 'text',
                        'strip': True,
                    },
                    'latest_release_date': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'current_version': {
                        'operator': 'changed',
                    },
                    'lts_version': {
                        'operator': 'changed',
                    }
                }
            },
            'React Documentation': {
                'selectors': {
                    'version': 'nav button[aria-label*="React version"]',
                    'latest_blog_post': 'main article h2 a',
                    'announcement_banner': '[role="banner"] + div[class*="announcement"]',
                },
                'normalization': {
                    'version': {
                        'type': 'text',
                        'strip': True,
                    },
                    'latest_blog_post': {
                        'type': 'text',
                        'strip': True,
                    },
                    'announcement_banner': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'version': {
                        'operator': 'changed',
                    }
                }
            },
            'Python Release Notes': {
                'selectors': {
                    'latest_version': '.download-os-windows .download-buttons a:first-child strong',
                    'latest_release_date': '.download-os-windows p:contains("Release Date:")',
                    'all_releases': '.list-row-container .row:first-child h2',
                },
                'normalization': {
                    'latest_version': {
                        'type': 'text',
                        'strip': True,
                    },
                    'latest_release_date': {
                        'type': 'text',
                        'strip': True,
                        'regex': r'Release Date:\s*(.+)',
                    },
                    'all_releases': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'latest_version': {
                        'operator': 'changed',
                    }
                }
            },
            'ICANN Fellowship Program': {
                'selectors': {
                    'application_status': 'main article:contains("application") h2, main article:contains("Application") h2',
                    'deadline': 'main article:contains("deadline") p, main article:contains("Deadline") p',
                    'program_info': 'main .intro-text',
                },
                'normalization': {
                    'application_status': {
                        'type': 'text',
                        'strip': True,
                    },
                    'deadline': {
                        'type': 'text',
                        'strip': True,
                    },
                    'program_info': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'application_status': {
                        'operator': 'contains',
                        'value': 'open'
                    }
                }
            },
            'Mastercard Foundation Scholars': {
                'selectors': {
                    'application_status': 'main h1:contains("Apply"), main h2:contains("Application")',
                    'eligibility': 'main section:contains("eligibility") p',
                    'deadline_info': 'main p:contains("deadline"), main p:contains("Deadline")',
                },
                'normalization': {
                    'application_status': {
                        'type': 'text',
                        'strip': True,
                    },
                    'eligibility': {
                        'type': 'text',
                        'strip': True,
                    },
                    'deadline_info': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'application_status': {
                        'operator': 'contains',
                        'value': 'open'
                    }
                }
            },
            'MLH Fellowship - Open Source': {
                'selectors': {
                    'application_status': 'main button:contains("Apply"), main a:contains("Apply")',
                    'next_cohort': 'main h2:contains("cohort"), main h3:contains("Cohort")',
                    'deadline': 'main p:contains("deadline"), main span:contains("deadline")',
                },
                'normalization': {
                    'application_status': {
                        'type': 'exists',
                    },
                    'next_cohort': {
                        'type': 'text',
                        'strip': True,
                    },
                    'deadline': {
                        'type': 'text',
                        'strip': True,
                    }
                },
                'alert_on': {
                    'application_status': {
                        'operator': 'equals',
                        'value': True
                    }
                }
            },
            'Mozilla Fellowships': {
                'selectors': {
                    'fellowship_status': 'main h2:contains("Fellowship"), main h1:contains("Fellowship")',
                    'nomination_info': 'main p:contains("nomination"), main p:contains("apply")',
                    'current_fellows': 'main section:contains("Fellows") h3',
                },
                'normalization': {
                    'fellowship_status': {
                        'type': 'text',
                        'strip': True,
                    },
                    'nomination_info': {
                        'type': 'text',
                        'strip': True,
                    },
                    'current_fellows': {
                        'type': 'count',
                    }
                },
                'alert_on': {
                    'nomination_info': {
                        'operator': 'contains',
                        'value': 'open'
                    }
                }
            },
        }

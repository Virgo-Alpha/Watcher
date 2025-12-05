"""
Management command to fix all broken haunt selectors with working configurations.
Updates existing haunts with proper CSS selectors that match actual DOM structures.
Configurations are designed to be human-like and specific to what each site does.
"""
import logging
from django.core.management.base import BaseCommand
from apps.haunts.models import Haunt

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix all broken haunt selectors with working configurations based on actual site structures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Define working configurations for each problematic haunt
        # These are based on actual site structures and designed like a human would configure them
        haunt_configs = {
            'GitHub Status': {
                'description': 'Monitor GitHub service status - is everything operational?',
                'config': {
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
                }
            },
            
            'AWS Service Health': {
                'description': 'Monitor AWS service health dashboard for any service disruptions',
                'config': {
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
                }
            },

            'Google Summer of Code Timeline': {
                'description': 'Monitor GSoC timeline for application period dates and deadlines',
                'config': {
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
                }
            },

            'Node.js Releases': {
                'description': 'Monitor Node.js for new LTS and current releases',
                'config': {
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
                }
            },

            'React Documentation': {
                'description': 'Monitor React docs for version updates and major announcements',
                'config': {
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
                }
            },

            'Python Release Notes': {
                'description': 'Check for new Python version releases and security updates',
                'config': {
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
                }
            },

            'ICANN Fellowship Program': {
                'description': 'Monitor ICANN Fellowship application status and deadlines',
                'config': {
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
                }
            },

            'Mastercard Foundation Scholars': {
                'description': 'Check if Mastercard Foundation scholarship applications are open',
                'config': {
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
                }
            },

            'MLH Fellowship - Open Source': {
                'description': 'Check if MLH Fellowship applications are open for the next cohort',
                'config': {
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
                }
            },

            'Mozilla Fellowships': {
                'description': 'Check if Mozilla Fellowship nominations are open',
                'config': {
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
                }
            },

            'Miles Morland Foundation': {
                'description': 'Monitor Miles Morland Foundation for writing grant applications',
                'config': {
                    'selectors': {
                        'grant_status': 'main h2:contains("Grant"), main h1:contains("Grant")',
                        'application_info': 'main p:contains("application"), main div:contains("apply")',
                        'deadline': 'main p:contains("deadline"), main strong:contains("deadline")',
                    },
                    'normalization': {
                        'grant_status': {
                            'type': 'text',
                            'strip': True,
                        },
                        'application_info': {
                            'type': 'text',
                            'strip': True,
                        },
                        'deadline': {
                            'type': 'text',
                            'strip': True,
                        }
                    },
                    'alert_on': {
                        'application_info': {
                            'operator': 'contains',
                            'value': 'open'
                        }
                    }
                }
            },

            'PyCon US 2026': {
                'description': 'Monitor PyCon US 2026 for CFP and registration dates',
                'config': {
                    'selectors': {
                        'cfp_status': 'main a:contains("Call for Proposals"), main button:contains("Submit")',
                        'registration_status': 'main a:contains("Register"), main button:contains("Registration")',
                        'important_dates': 'main section:contains("dates") ul li, main h2:contains("Dates") + ul li',
                    },
                    'normalization': {
                        'cfp_status': {
                            'type': 'exists',
                        },
                        'registration_status': {
                            'type': 'exists',
                        },
                        'important_dates': {
                            'type': 'text',
                            'strip': True,
                        }
                    },
                    'alert_on': {
                        'cfp_status': {
                            'operator': 'equals',
                            'value': True
                        },
                        'registration_status': {
                            'operator': 'equals',
                            'value': True
                        }
                    }
                }
            },
        }
        
        updated_count = 0
        not_found_count = 0
        skipped_count = 0
        
        for haunt_name, haunt_data in haunt_configs.items():
            try:
                # Get all haunts with this name
                haunts = Haunt.objects.filter(name=haunt_name)
                
                if haunts.count() == 0:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Not found: {haunt_name}')
                    )
                    not_found_count += 1
                    continue
                
                if haunts.count() > 1:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Multiple haunts found for {haunt_name} ({haunts.count()}), updating all')
                    )
                
                # Update all matching haunts
                for haunt in haunts:
                    
                    if dry_run:
                        self.stdout.write(f'\n📋 Would update: {haunt_name} (ID: {haunt.id})')
                        self.stdout.write(f'   Owner: {haunt.owner.email}')
                        self.stdout.write(f'   URL: {haunt.url}')
                        self.stdout.write(f'   Description: {haunt_data["description"]}')
                        self.stdout.write(f'   Selectors: {list(haunt_data["config"]["selectors"].keys())}')
                    else:
                        haunt.description = haunt_data['description']
                        haunt.config = haunt_data['config']
                        haunt.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Updated: {haunt_name} (ID: {haunt.id})')
                        )
                        self.stdout.write(f'   Owner: {haunt.owner.email}')
                        self.stdout.write(f'   Selectors: {", ".join(haunt_data["config"]["selectors"].keys())}')
                    
                    updated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error updating {haunt_name}: {str(e)}')
                )
                skipped_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🔍 DRY RUN COMPLETE'
                    f'\n  • Would update: {updated_count} haunts'
                    f'\n  • Not found: {not_found_count} haunts'
                    f'\n  • Skipped (errors): {skipped_count} haunts'
                    f'\n\nRun without --dry-run to apply changes'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ UPDATE COMPLETE'
                    f'\n  • Updated: {updated_count} haunts'
                    f'\n  • Not found: {not_found_count} haunts'
                    f'\n  • Skipped (errors): {skipped_count} haunts'
                )
            )

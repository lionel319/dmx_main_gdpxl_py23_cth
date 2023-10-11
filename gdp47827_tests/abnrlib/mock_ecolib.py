class MockProduct(object):
    def __init__(self, family, product):
        self._family = family
        self._product = product
        self._roadmap = product
        self._revisions = ''
        self._milestones = ''
    def get_product_properties(self):
        return self._roadmap
    @property
    def roadmap(self):
        return self._roadmap              
    @property
    def product(self):
        return self._product          
    def get_revisions(self):
        return self._revisions
    def get_milestones(self):
        return self._milestones              

class MockFamily(object):
    def __init__(self, family):
        self._family = family
        self._icmgroup = 'icmgroup'
    @property                
    def icmgroup(self):
        return self._icmgroup    
    @property                
    def family(self):
        return self._family
    def get_product(self, _anything):
        return MockProduct(self._family, "RM1")
    def get_ip(self, _anything, project_filter=''):
        return MockIP(self._family, 'IP')
    def get_roadmap(self, _anything):
        return MockRoadmap(self._family, 'Roadmap')
    def verify_roadmap(self, milestone, thread):
        return True

class MockIP(object):
    def __init__(self, family, ip):
        self.roadmap = "RM1"
        self._ip = ip
        self._iptype = ''
    @property
    def ip(self):
        return self._ip  
    @property
    def iptype(self):
        return self._iptype 
    @iptype.setter
    def iptype(self, iptype):
        self._iptype = iptype
    def get_deliverable(self, deliverable, roadmap='', milestone='99'):
        return MockDeliverable('Deliverable')
    def get_unneeded_deliverables(self, local=False, bom='dev', roadmap='RM1'):
        return []
    def get_all_deliverables(self, milestone, roadmap=''):
        return [MockDeliverable('Deliverable')]
        
class MockIPType(object):
    def __init__(self, family, iptype):
        self._iptype = iptype
    @property
    def iptype(self):
        return self._iptype             
    def get_deliverable(self, deliverable, roadmap=''):    
        return MockDeliverable('Deliverable')

class MockDeliverable(object):
    def __init__(self, deliverable):
        self._deliverable = deliverable
    @property
    def deliverable(self):
        return self._deliverable    
    @property
    def large(self):
        return False
    @property
    def large_excluded_ip(self):
        return []
    @property
    def dm(self):
        return 'icmanage'
    @property
    def dm_meta(self):
        return dict()

class MockRoadmap(object):
    def __init__(self, family, roadmap):
        self._roadmap = roadmap
    @property
    def roadmap(self):
        return self._roadmap
    def is_subset(self, roadmap, milestone):
        return True

class MockRevision(object):
    def __init__(self, revision):
        self._revision = 'rev{}'.format(revision)

    @property
    def revision(self):
        return self._revision

class MockMilestone(object):
    def __init__(self, milestone):
        self._milestone = milestone

    @property
    def milestone(self):
        return self._milestone    


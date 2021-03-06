# encoding: utf-8
import logging

from sqlalchemy import orm, types, Column, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation

import ckan.plugins as p

from ckan.common import _
from ckan.model import meta
from ckan.model import core
from ckan.model import package as _package
from ckan.model import types as _types
from ckan.model import domain_object
from ckan.model.meta import metadata, engine

from .interfaces import IRelationships

Base = declarative_base(metadata=metadata)

__all__ = ['PackageRelationship', 'Relationship', ]


log = logging.getLogger(__name__)


class Relationship(Base):
    __tablename__ = 'package_relationship_dev'

    _id = Column('id', types.UnicodeText, primary_key=True,
                 default=_types.make_uuid)
    subject_package_id = Column(types.UnicodeText, ForeignKey('package.id'))
    object_package_id = Column(types.UnicodeText, ForeignKey('package.id'))
    _type = Column('type', types.UnicodeText)
    comment = Column(types.UnicodeText)
    state = Column(types.UnicodeText, default=core.State.ACTIVE)


class PackageRelationship(core.StatefulObjectMixin,
                          domain_object.DomainObject):
    '''The rule with PackageRelationships is that they are stored in the model
    always as the "forward" relationship - i.e. "child_of" but never
    as "parent_of". However, the model functions provide the relationships
    from both packages in the relationship and the type is swapped from
    forward to reverse accordingly, for meaningful display to the user.'''

    # List of (type, corresponding_reverse_type)
    # e.g. (A is "child_of" B, B is a "parent_of" A)
    # don't forget to add specs to Solr's schema.xml
    # types = [(u'depends_on', u'dependency_of'),
    #          (u'derives_from', u'has_derivation'),
    #          (u'links_to', u'linked_from'),
    #          (u'child_of', u'parent_of'),
    #          ]
    types = [
        (u'child_of', u'parent_of'),
        (u'sibling_of', u'sibling_of')
    ]
    for plugin in p.PluginImplementations(IRelationships):
        types = plugin.get_rel_types()

    # types_printable = \
    #         [(_(u'depends on %s'), _(u'is a dependency of %s')),
    #          (_(u'derives from %s'), _(u'has derivation %s')),
    #          (_(u'links to %s'), _(u'is linked from %s')),
    #          (_(u'is a child of %s'), _(u'is a parent of %s')),
    #          ]
    types_printable = [
        (u'is a child of {}', u'is a parent of {}'),
        (u'is a sibling of {}', u'is a sibling of {}')
    ]

    for plugin in p.PluginImplementations(IRelationships):
        types = plugin.get_printable_rel_types()

    # inferred_types_printable = \
    #         {'sibling':_('has sibling %s')}

    def __str__(self):
        state = "*" if self.active != core.State.ACTIVE else ""
        return f'<{state}PackageRelationship {self.subject.name} \
                {self.type} {self.object.name}>'

    def __repr__(self):
        return str(self)

    def as_dict(self, package=None, ref_package_by='id'):
        """Returns full relationship info as a dict from the point of view
        of the given package if specified.
        e.g. {'subject':u'annakarenina',
              'type':u'depends_on',
              'object':u'warandpeace',
              'comment':u'Since 1843'}"""

        relationship_type = self.type
        if package and package == object_pkg:
            subject_pkg = self.object
            object_pkg = self.subject
            relationship_type = self.forward_to_reverse_type(self.type)
        subject_ref = getattr(subject_pkg, ref_package_by)
        object_ref = getattr(object_pkg, ref_package_by)
        return {
            'subject': subject_ref,
            'type': relationship_type,
            'object': object_ref,
            'comment': self.comment
        }

    def as_tuple(self, package):
        '''Returns basic relationship info as a tuple from the point of view
        of the given package with the object package object.
        e.g. rel.as_tuple(warandpeace) gives (u'depends_on', annakarenina)
        meaning warandpeace depends_on annakarenina.'''
        assert isinstance(package, _package.Package), package
        if self.subject == package:
            type_str = self.type
            other_package = self.object
        elif self.object == package:
            type_str = self.forward_to_reverse_type(self.type)
            other_package = self.subject
        else:
            # FIXME do we want a more specific error
            raise Exception('Package %s is not in this relationship: %s' %
                            (package, self))
        return (type_str, other_package)

    @classmethod
    def by_subject(cls, package):
        return meta.Session.query(cls).filter(
            cls.subject_package_id == package.id)

    @classmethod
    def by_object(cls, package):
        return meta.Session.query(cls).filter(
            cls.object_package_id == package.id)

    @classmethod
    def get_forward_types(cls):
        if not hasattr(cls, 'fwd_types'):
            cls.fwd_types = [fwd for fwd, rev in cls.types]
        return cls.fwd_types

    @classmethod
    def get_reverse_types(cls):
        if not hasattr(cls, 'rev_types'):
            cls.rev_types = [rev for fwd, rev in cls.types]
        return cls.rev_types

    @classmethod
    def get_all_types(cls):
        if not hasattr(cls, 'all_types'):
            cls.all_types = []
            for fwd, rev in cls.types:
                cls.all_types.append(fwd)
                cls.all_types.append(rev)
        return cls.all_types

    @classmethod
    def reverse_to_forward_type(cls, reverse_type):
        for fwd, rev in cls.types:
            if rev == reverse_type:
                return fwd

    @classmethod
    def forward_to_reverse_type(cls, forward_type):
        for fwd, rev in cls.types:
            if fwd == forward_type:
                return rev

    @classmethod
    def is_undirect(cls, forward_or_reverse_type):
        for fwd, rev in cls.types:
            if (rev == forward_or_reverse_type
                    and fwd == forward_or_reverse_type):
                return fwd

    @classmethod
    def reverse_type(cls, forward_or_reverse_type):
        for fwd, rev in cls.types:
            if fwd == forward_or_reverse_type:
                return rev
            if rev == forward_or_reverse_type:
                return fwd

    @classmethod
    def make_type_printable(cls, type_):
        for i, types in enumerate(cls.types):
            for j in range(2):
                if type_ == types[j]:
                    return cls.types_printable[i][j]
        raise TypeError(type_)


meta.mapper(PackageRelationship, Relationship.__table__, properties={
    'subject': orm.relation(_package.Package, primaryjoin=Relationship.__table__.c.subject_package_id == _package.Package.id,
                            backref='relationships_as_subject'),
    'object': orm.relation(_package.Package, primaryjoin=Relationship.__table__.c.object_package_id == _package.Package.id,
                           backref='relationships_as_object'),
})


def create_tables():
    """
    Creates the necessary database tables
    """
    log.debug("Creating relationships database tables")
    Base.metadata.create_all(engine)


def drop_tables():
    """
    Drop all tables
    """
    log.debug("Deleting relationships database tables")
    Base.metadata.drop_all(engine, tables=[Relationship.__table__, ])

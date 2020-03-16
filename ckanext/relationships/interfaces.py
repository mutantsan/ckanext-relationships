import ckan.plugins.interfaces as interfaces


class IRelationships(interfaces.Interface):
    '''Allow modifying package Relationships'''

    def get_rel_types(self):
        '''
        Provides an ability to define own types of relationships
        between packages in additional of existed "child_of"-"parent_of"

        The relationships should be provided as a pair of object-subject

        If object and subject are equal, then the non-directional
        relationship type will be created.

        :param data_dict: the relationship types mapping
        :type data_dict: dictionary

        rels = [
            ("depends_on", "derives_from"),
            ("links_to", "linked_from"),
            ("siblings", "siblings")
        ]
        '''
        return rel_dict

    def get_printable_rel_types(self):
        '''
        Printable view of relationship types. Must be provided with get_rel_types

        :param data_dict: printable relationship types mapping
        :type data_dict: dictionary

        printable_rels = [
            ("depends on {}", "is a dependency of {}"),
            ("links to {}", "is linked from {}"),
            ("is a child of {}", "is a parent of {}")
        ]
        '''
        return rel_printable_dict
# -*- coding: utf-8 -*-

"""
    ldapom_model
    ------------

    This module provide a base class to manage models with ldapom.

    :copyright: (c) 2014 by Guillaume Subiron.
"""

from ldapom import LDAPEntry


__all__ = ['LDAPAttr', 'LDAPModel']


class MultipleResultsFound(Exception):
    """Raised when multiple results are found, but only one was excepted."""
    pass


class NoResultFound(Exception):
    """Raised when no result is found."""
    pass


class MultipleValuesInAttribute(Exception):
    """Raised the attribute has multiple values, but only one was excepted."""
    pass


class LDAPAttr():
    """LDAP Attribute."""

    def __init__(self, attr, multiple=False, nullable=True):
        """
            Instanciates a new LDAPAttr.

            :param attr: Attribute name in the LDAP
            :param multiple: Is it a multiple values attribute? default=False
            :param nullable: May be null? default=True
        """
        self.attr = attr
        self.multiple = multiple
        self.nullable = nullable


class LDAPModel():
    """
        LDAP Model.
        Inherit this class to create a model abstracting LDAP entries. You
        will have to specify some attributes:

        :attr _class: objectClass corresponding to your model in the LDAP.
        :attr _class_attrs: Dictionary of attributes to retrieve. Keys are
                            the names of attributes in your model, and values
                            are LDAPAttr matching the attributes in the LDAP.
                            'dn' and 'objectClass' attributes are automatically
                            added to the dictionary.
        :attr _rdn: Relative Distinguished Name of the entries. default="cn"

        :Example:

        class Person(LDAPModel):
            _class = 'inetOrgPerson'
            _class_attrs = {'cn': LDAPAttr('cn'),
                            'mail': LDAPAttr('mail'),
                            'lastname': LDAPAttr('sn'),
                            'firstname': LDAPAttr('givenName'),
                            'phone': LDAPAttr('telephoneNumber')}
    """

    _attrs = {'objectClass': LDAPAttr('objectClass',
                                      multiple=True, nullable=False),
              'dn': LDAPAttr('dn')}
    _class_attrs = dict()
    _class = ""
    _rdn = "cn"
    _entry = None

    def _preprocess_attrs(self, kwargs):
        """
            Returns a preprocessed dictionary of attributes. Used by default
            before using the _class_attrs dict.

            :param kwargs: a dictionary of attributes
        """
        if kwargs:
            if 'objectClass' not in kwargs:
                kwargs['objectClass'] = [self._class]
            elif self._class not in kwargs['objectClass']:
                kwargs['objectClass'].append(self._class)
        return kwargs

    def __init__(self, connection, dn, **kwargs):
        """
            Instanciate a new object. Return an unsaved instance of the model.

            :param connection: ldapom.LDAPConnection object
            :param dn: Distinguished Name of the new object
            :param kwargs: attributes to set
        """
        self._attrs = dict(self._attrs, **self._class_attrs)
        self._entry = LDAPEntry(connection, dn)
        for k, v in self._preprocess_attrs(kwargs).items():
            setattr(self, k, v)

    def __repr__(self):
        return repr(self._entry)

    def __str__(self):
        return str(self._entry)

    def __setattr__(self, name, value):
        """
            Set an attribute value. Does'nt save the change in the LDAP.

            :param name: Must be a key of the _class_attrs dictionary.
            :param value: The new attribute value.
        """
        # Use normal behaviour if setting an existing instance attribute.
        if name in self.__dict__:
            return super(LDAPModel, self).__setattr__(name, value)

        if name in self._attrs:
            attr = self._attrs[name]
            if attr.multiple and type(value) is str:
                raise
            return setattr(self._entry, attr.attr, value)
        else:
            return super(LDAPModel, self).__setattr__(name, value)

    def __getattr__(self, name):
        """
            Get an attribute value.

            :param name: Must be a key of the _class_attrs dictionary.
        """
        if name in self._attrs:
            multiple = self._attrs[name].multiple
            attr = self._attrs[name].attr
            res = getattr(self._entry, attr)
            if multiple:
                return res
            else:
                if type(res) is str or type(res) is int or type(res) is float:
                    return res
                if len(res) == 0:
                    return None
                if len(res) == 1:
                    return list(res)[0]
                raise MultipleValuesInAttribute()
        else:
            raise AttributeError()

    def __delattr__(self, name):
        if name in self._attrs:
            name = self._attrs[name]['attr']
            del self._entry.name

    def save(self):
        """
            Save this entry and its attributes to the LDAP server.
        """
        return self._entry.save()

    @classmethod
    def _from_entry(cls, entry):
        obj = cls(None, "")
        obj._entry = entry
        obj._entry.fetch()
        return obj

    @classmethod
    def search(cls, connection, **kwargs):
        """
            Return a list of entries.

            :param connection: ldapom.LDAPConnection object
            :param kwargs: Attributes to search. Entries must match all the
                           attributes (&)
        """
        search_filter = "(&(objectClass=%s)%s)" % (cls._class, cls._kwargs_to_filter(kwargs))
        return cls._search(connection, search_filter=search_filter)

    @classmethod
    def _search(cls, connection, **kwargs):
        """
            Return a list of entries.

            :param connection: ldapom.LDAPConnection object
            :param search_filter: ldapsearch-style search filter
            :param retrieve_attributes: List of attributes to retrieve. If None is
                                        given, all are retrieved.
            :param base: Search base for the query.
            :param scope: The search scope in the LDAP tree
        """
        for r in connection.search(**kwargs):
            yield cls._from_entry(r)

    @classmethod
    def retrieve(cls, connection, id):
        """
            Retrieve the entry.

            :param connection: ldapom.LDAPConnection object
            :param id: id of the entry to retrieve. (_rdn=id)
        """
        filters = {cls._rdn: id}
        res = list(cls.search(connection, **filters))
        if len(res) == 1:
            return res[0]
        elif len(res) == 0:
            raise NoResultFound()
        else:
            raise MultipleResultsFound()

    @staticmethod
    def _kwargs_to_filter(kwargs):
        """
            Return a ldapsearch-style search filter.

            :param kwargs: Attributes to use in the search_filter.
        """
        if kwargs:
            f = ""
            for k, v in kwargs.items():
                f += ("(%s=%s)" % (k, v))
            return "(&%s)" % f
        return ""

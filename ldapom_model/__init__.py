# -*- coding: utf-8 -*-

"""
    ldapom_model
    ------------

    This module provide a base class to manage models with ldapom.

    :copyright: (c) 2014 by Guillaume Subiron.
"""

import copy

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


class AttributeNotFound(Exception):
    """Raised when the attribute is not found in the entry, unless if default
       is set."""
    pass


class NotNullableAttribute(Exception):
    """Raised when the attribute is not nullable and the user is trying to a
       None value."""
    pass


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class LDAPAttr():
    """LDAP Attribute."""

    def __init__(self, attr, multiple=False, nullable=True, default=None, server_default=None):
        """
            Instanciates a new LDAPAttr.

            :param attr: Attribute name in the LDAP
            :param multiple: Is it a multiple values attribute? default=False
            :param nullable: May be null? default=True
            :param default: Default value for the attribute is it is not set
                            on the server.
            :param server_default: Value to set on the server if the attribute
                                   is not defined.
        """
        self.attr = attr
        self.multiple = multiple
        self.nullable = nullable
        self.default = default
        self.server_default = server_default


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

    __attrs = {'objectClass': LDAPAttr('objectClass',
                                       multiple=True, nullable=False),
               'dn': LDAPAttr('dn')}
    _class_attrs = dict()
    _class = ""
    _rdn = "cn"
    _entry = None

    @ClassProperty
    @classmethod
    def _attrs(cls):
        return dict(cls.__attrs, **cls._class_attrs)

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
        #self._attrs = dict(self._attrs, **self._class_attrs)
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
            #if attr.multiple and type(value) is str:
                #raise
            if not attr.nullable and value is None:
                raise NotNullableAttribute()
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
            default = self._attrs[name].default
            try:
                res = getattr(self._entry, attr)
            except AttributeError:
                if default is not None:
                    res = default
                else:
                    raise AttributeNotFound()
            if multiple:
                return res
            else:
                if type(res) is str or type(res) is int or type(res) is float or type(res) is bool:
                    return res
                if len(res) == 0:
                    return default
                if len(res) == 1:
                    return list(res)[0]
                raise MultipleValuesInAttribute()
        else:
            raise AttributeError()

    def __delattr__(self, name):
        if name in self._attrs:
            name = self._attrs[name].attr
            delattr(self._entry, name)

    def save(self):
        """
            Save this entry and its attributes to the LDAP server.
        """
        for name, default_value in {n: a.server_default for n, a in self._attrs.items() if a.server_default is not None}.items():
            try:
                value = getattr(self, name)
            except AttributeNotFound:
                value = None
            if not value and value is not False and value is not 0:
                setattr(self, name, default_value)
        return self._entry.save()

    def delete(self):
        """
           Delete this entry on the LDAP server.
        """
        return self._entry.delete()

    @classmethod
    def search(cls, connection, **kwargs):
        """
            Return a list of entries.

            :param connection: ldapom.LDAPConnection object
            :param kwargs: Attributes to search. Entries must match all the
                           attributes (&)
        """
        for k, v in kwargs.items():
            if k in cls._attrs:
                kwargs.pop(k)
                kwargs[cls._attrs[k].attr] = v
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
        if not "search_filter" in kwargs:
            kwargs['search_filter'] = "(objectClass=%s)" % cls._class
        for entry in connection.search(**kwargs):
            obj = cls(None, "")
            obj._entry = entry
            # Copy fetched_attributes because search() doesn't do it and
            # LDAPEntry.search is doing a new ldap search.
            obj._entry._fetched_attributes = copy.deepcopy(obj._entry._attributes)
            yield obj

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

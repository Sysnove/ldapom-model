# -*- coding: utf-8 -*-
 
"""
    Base class to manage models with ldapom.
"""

from ldapom import LDAPEntry


class MultipleResultsFound(Exception):
    pass


class NoResultFound(Exception):
    pass


class MultipleValuesInAttribute(Exception):
    pass


__all__ = ['LDAPAttr', 'LDAPModel']


class LDAPAttr():
    def __init__(self, attr, multiple=False, nullable=True):
        self.attr = attr
        self.multiple = multiple
        self.nullable = nullable


class LDAPModel():
    _attrs = {'objectClass': LDAPAttr('objectClass',
                                      multiple=True, nullable=False),
              'dn': LDAPAttr('dn')}
    _class_attrs = dict()
    _class = ""
    _rdn = "cn"
    _entry = None

    def _preprocess_attrs(self, kwargs):
        if kwargs:
            if 'objectClass' not in kwargs:
                kwargs['objectClass'] = [self._class]
            elif self._class not in kwargs['objectClass']:
                kwargs['objectClass'].append(self._class)
        return kwargs

    def __init__(self, connection, dn, **kwargs):
        self._attrs = dict(self._attrs, **self._class_attrs)
        self._entry = LDAPEntry(connection, dn)
        for k, v in self._preprocess_attrs(kwargs).items():
            setattr(self, k, v)

    def __repr__(self):
        return repr(self._entry)

    def __str__(self):
        return str(self._entry)

    def __setattr__(self, name, value):
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
        if name in self._attrs:
            multiple = self._attrs[name].multiple
            attr = self._attrs[name].attr
            res = getattr(self._entry, attr)
            if multiple:
                return res
            else:
                if type(res) is str:
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
        return self._entry.save()

    @classmethod
    def _from_entry(cls, entry):
        obj = cls(None, "")
        obj._entry = entry
        obj._entry.fetch()
        return obj

    @classmethod
    def search(cls, connection, **kwargs):
        search_filter = "(&(objectClass=%s)%s)" % (cls._class, cls._kwargs_to_filter(kwargs))
        return cls._search(connection, search_filter)

    @classmethod
    def _search(cls, connection, search_filter):
        for r in connection.search(search_filter=search_filter):
            yield cls._from_entry(r)

    @classmethod
    def retrieve(cls, connection, id):
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
        if kwargs:
            f = ""
            for k, v in kwargs.items():
                f += ("(%s=%s)" % (k, v))
            return "(&%s)" % f
        return ""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from ldapom import LDAPConnection
from ldapom_model import LDAPModel, LDAPAttr, NoResultFound, AttributeNotFound, NotNullableAttribute, MultipleResultsFound
import ldapom
import test_server

class LDAPServerMixin(object):

    """Mixin to set up an LDAPConnection connected to a testing LDAP server."""

    def setUp(self):
        self.ldap_server = test_server.LDAPServer()
        self.ldap_server.start()
        self.ldap = LDAPConnection(
                uri=self.ldap_server.ldapi_url(),
                base='dc=example,dc=com',
                bind_dn='cn=admin,dc=example,dc=com',
                bind_password='admin')

    def tearDown(self):
        self.ldap_server.stop()


class Person(LDAPModel):
    _class = 'person'
    _class_attrs = {'cn': LDAPAttr('cn'),
                    'lastname': LDAPAttr('sn', server_default="Default"),
                    'invalidAttribute': LDAPAttr('invalid'),
                    'shell': LDAPAttr('loginShell'),
                    'phone': LDAPAttr('telephoneNumber', multiple=True),
                    'home': LDAPAttr('homeDirectory', nullable=False),
                    'description': LDAPAttr('description', default="Default"),
                    'photo': LDAPAttr('jpegPhoto')}
    _rdn = 'cn'

    def __str__(self):
        return self.name

    @property
    def name(self):
        return ' '.join([self.givenName, self.sn]) if self.givenName else self.sn


class Test(LDAPServerMixin, unittest.TestCase):

    def test_ok(self):
        self.assertTrue(True)

    def test_retrieve(self):
        Person.retrieve(self.ldap, "jack")
        with self.assertRaises(NoResultFound):
            Person.retrieve(self.ldap, "nobody")
        with self.assertRaises(MultipleResultsFound):
            Person.retrieve(self.ldap, "*a*")

    def test_create(self):
        p = Person(self.ldap, 'cn=george,dc=example,dc=com', cn="george", lastname="Hammond")
        p.save()
        p = Person.retrieve(self.ldap, "george")
        self.assertEqual(p.lastname, "Hammond")

    def test_delete(self):
        p = Person.retrieve(self.ldap, "jack")
        self.assertTrue(p._entry.exists())
        p.delete()
        self.assertFalse(p._entry.exists())

    def test_default_attribute(self):
        p = Person(self.ldap, 'cn=george,dc=example,dc=com', cn="george", lastname="Hammond")
        p.save()
        self.assertEqual(p.description, "Default")
        self.assertEqual(p._entry.description, set())
        p.description = "Test"
        p.save()
        p = Person.retrieve(self.ldap, "george")
        self.assertEqual(p.description, "Test")

    def test_server_default_attribute(self):
        p = Person(self.ldap, 'cn=george,dc=example,dc=com', cn="george")
        p.save()
        self.assertEqual(p.lastname, "Default")
        self.assertEqual(p._entry.sn, {"Default"})
        p.lastname = "Hammond"
        p.save()
        p = Person.retrieve(self.ldap, "george")
        self.assertEqual(p.lastname, "Hammond")

    def test_new_invalid_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        with self.assertRaises(ldapom.error.LDAPAttributeNameNotFoundError):
            p.invalidAttribute = 'invalid'

    def test_modify_single_value_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.shell, "/bin/bash")
        p.shell = "/bin/zsh"
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.shell, "/bin/zsh")
        p.shell = ""
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.shell, "")
        p.shell = None
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        with self.assertRaises(AttributeNotFound):
            p.shell

    def test_modify_multi_value_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        p.phone = "0000000000"
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, {"0000000000"})
        p.phone = ["0000000000", "1111111111"]
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, {"0000000000", "1111111111"})
        p.phone.add("2222222222")
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, {"0000000000", "1111111111", "2222222222"})
        p.phone = []
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, set())

    def test_modify_notnullable_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.home, "/home/jack")
        p.home = "/home/oniel"
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.home, "/home/oniel")
        p.home = ""
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.home, "")
        with self.assertRaises(NotNullableAttribute):
            p.home = None

    def test_delete_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        del p.shell
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        with self.assertRaises(AttributeNotFound):
            p.shell

    def test_search(self):
        people = list(Person.search(self.ldap))
        self.assertEqual(len(people), 4)
        people = list(Person.search(self.ldap, sn="Carter"))
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0].cn, "sam")
        people = list(Person.search(self.ldap, sn="nobody"))
        self.assertEqual(len(people), 0)


if __name__ == '__main__':
    unittest.main()

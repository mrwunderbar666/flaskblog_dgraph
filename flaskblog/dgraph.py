import json
import datetime
import math
from dateutil import parser as dateparser
import os

from flask import current_app, _app_ctx_stack, Markup
import pydgraph

class DGraph(object):
    '''Class for dgraph database connection'''

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        app.config.setdefault('DGRAPH_ENDPOINT', 'localhost:9080')
        app.config.setdefault('DGRAPH_CREDENTIALS', None)
        app.config.setdefault('DGRAPH_OPTIONS', None)

        app.logger.info(f"Establishing connection to DGraph: {app.config['DGRAPH_ENDPOINT']}")

        self._app = app
        self.client_stub = pydgraph.DgraphClientStub(app.config['DGRAPH_ENDPOINT'], 
                                                        credentials=app.config['DGRAPH_CREDENTIALS'],
                                                        options=app.config['DGRAPH_OPTIONS'])

        self.client = pydgraph.DgraphClient(self.client_stub)


    def close(self, *args):
        # Close each DGraph client stub
        self.client_stub.close()


    def teardown(self, exception):
        self._app.logger.info(f"Closing Connection: {self._app.config['DGRAPH_ENDPOINT']}")
        self.client_stub.close()

    def query(self, query_string, variables=None):
        self._app.logger.debug(f"Sending dgraph query.")
        if variables is None:
            res = self.client.txn(read_only=True).query(query_string)
        else:
            res = self.client.txn(read_only=True).query(query_string, variables=variables)
        self._app.logger.debug(f"Received response for dgraph query.")
        data = json.loads(res.json)
        return data
    
    def get_uid(self, field, value):
        query_string = f'{{ q(func: eq({field}, {value})) {{ uid {field} }} }}'
        data = self.query(query_string)
        if len(data['q']) == 0:
            return None
        return data['q'][0]['uid']

    def get_user(self, **kwargs):

        uid = kwargs.get('uid', None)
        username = kwargs.get('username', None)
        email = kwargs.get('email', None)

        if uid:
            query_func = f'{{ q(func: uid({uid}))'
        elif email:
            query_func = f'{{ q(func: eq(email, "{email}"))'
        elif username:
            query_func = f'{{ q(func: eq(username, "{username}"))'
        else:
            raise ValueError()

        query_fields =  f'{{ uid username email avatar_img date_joined }} }}'
        query_string = query_func + query_fields
        data = self.query(query_string)
        if len(data['q']) == 0:
            return None
        data = data['q'][0]
        data['date_joined'] = dateparser.parse(data['date_joined'])
        return data


    def user_login(self, email, pw):
        query_string = f'{{login_attempt(func: eq(email, "{email}")) {{ checkpwd(pw, {pw}) }} }}'
        result = self.query(query_string)
        if len(result['login_attempt']) == 0:
            return 'Invalid Email'
        else:
            return result['login_attempt'][0]['checkpwd(pw)']

    def create_user(self, user_data):
        if type(user_data) is not dict:
            raise TypeError()
        
        user_data['uid'] =  '_:newuser'
        user_data['dgraph.type'] = 'User'
        user_data['date_joined'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_data['avatar_img'] = os.path.join('default.jpg')
        
        txn = self.client.txn()

        try:
            response = txn.mutate(set_obj=user_data)
            txn.commit()
        except:
            response = False
        finally:
            txn.discard()

        if response:
            return response.uids['newuser']
        else: return False

    def update_entry(self, uid, input_data):
        if type(input_data) is not dict:
            raise TypeError()
        
        input_data['uid'] =  uid
        
        txn = self.client.txn()

        try:
            response = txn.mutate(set_obj=input_data)
            txn.commit()
        except:
            response = False
        finally:
            txn.discard()

        if response:
            return True
        else: return False

    def delete_entry(self, uid):

        mutation = {'uid': uid}
        txn = self.client.txn()

        try:
            response = txn.mutate(del_obj=mutation)
            txn.commit()
        except:
            response = False
        finally:
            txn.discard()

        if response:
            return True
        else: return False

    def list_posts(self, per_page=3, page=1):

        offset = per_page * (page-1)

        query_func = f'{{ posts(func: type(Post), orderdesc: date_published, first: {per_page}, offset: {offset})' 
        query_fields = '''{ 
                            uid title content date_published 
                            author { uid username display_name avatar_img } 
                            tags category { uid name }
                            }
                        total(func: type(Post)) {
                            count(uid)
                        }
                            }'''
        
        query = query_func + query_fields

        res = self.client.txn(read_only=True).query(query)

        data = json.loads(res.json)
        posts = data['posts']
        total = data['total'][0]['count']
        pages = math.ceil(total / per_page)
        for item in posts:
            item['date_published'] = dateparser.parse(item['date_published'])
            item['content'] = Markup(item['content'].replace('\n', '</br>'))
        
        return posts, total, pages
    
    def list_user_posts(self, uid=None, username=None, per_page=3, page=1):
        if username:
            uid = self.get_uid('username', username)
        if uid is None:
            raise ValueError
        offset = per_page * (page-1)

        query_func = f'{{ posts(func: uid({uid}))' 
        query_user = '{ uid username display_name avatar_img '
        query_posts = f'pub_posts: ~author (orderdesc: date_published) (first: {per_page}) (offset: {offset})'
        query_posts_fields = '{ uid title content date_published tags category { uid name } author { uid username display_name avatar_img} }' 
        query_total_posts = 'total_posts: count(~author) } }'
                            
        query = query_func + query_user + query_posts + query_posts_fields + query_total_posts

        res = self.client.txn(read_only=True).query(query)

        data = json.loads(res.json)
        user = data['posts'][0]
        posts = data['posts'][0]['pub_posts']
        total = data['posts'][0]['total_posts']
        pages = math.ceil(total / per_page)
        for item in posts:
            item['date_published'] = dateparser.parse(item['date_published'])
            item['content'] = Markup(item['content'].replace('\n', '</br>'))
        
        return user, posts, total, pages

    def get_post(self, uid):

        query_uid = f'{{ post(func: uid({uid})) @filter(type("Post"))' 
        query_fields = '''{ 
                            uid title content date_published 
                            author { 
                                uid username display_name avatar_img 
                                } 
                            tags category { uid name }
                        } }'''
        
        query = query_uid + query_fields

        res = self.client.txn(read_only=True).query(query)

        data = json.loads(res.json)

        if len(data['post']) == 0:
            return False

        data = data['post'][0]
        data['date_published'] = dateparser.parse(data['date_published'])
        data['content_raw'] = data['content']
        data['content'] = Markup(data['content'].replace('\n', '</br>'))
        return data

    def create_post(self, post_data):
        if type(post_data) is not dict:
            raise TypeError()
        
        post_data['uid'] =  '_:newpost'
        post_data['dgraph.type'] = 'Post'
        post_data['date_published'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        txn = self.client.txn()

        try:
            response = txn.mutate(set_obj=post_data)
            txn.commit()
        except:
            response = False
        finally:
            txn.discard()

        if response:
            return response.uids['newpost']
        else: return False

import newsroom
import logging

from datetime import datetime
from flask import json, abort
from flask_babel import get_timezone
from eve.utils import ParsedRequest
from newsroom.auth import get_user
from newsroom.companies import get_user_company
from superdesk.utc import utc

logger = logging.getLogger(__name__)


aggregations = {
    'genre': {'terms': {'field': 'genre.name', 'size': 50}},
    'service': {'terms': {'field': 'service.name', 'size': 50}},
    'subject': {'terms': {'field': 'subject.name', 'size': 20}},
    'urgency': {'terms': {'field': 'urgency'}},
}


def get_user_timezone():
    """Get user timezone for date range query."""
    user_timezone = get_timezone()
    now = datetime.utcnow().replace(tzinfo=utc).astimezone(user_timezone)
    return now.strftime('%z')


class WireSearchResource(newsroom.Resource):
    datasource = {
        'search_backend': 'elastic',
        'source': 'items',
        'projection': {
            'slugline': 1,
            'headline': 1,
            'body_html': 1,
            'versioncreated': 1,
            'headline': 1,
            'nextversion': 1,
            'ancestors': 1,
        },
    }

    item_methods = ['GET']
    resource_methods = ['GET']


def get_aggregation_field(key):
    return aggregations[key]['terms']['field']


def set_service_query(query, company):
    if company and company.get('services'):
        services = [code for code, is_active in company['services'].items() if is_active]
        query['bool']['must'].append({'terms': {'service.code': services}})


class WireSearchService(newsroom.Service):
    def get(self, req, lookup):
        query = {
            'bool': {
                'must_not': [
                    {'term': {'type': 'composite'}},
                    {'constant_score': {'filter': {'exists': {'field': 'nextversion'}}}},
                ],
                'must': [],
            }
        }

        user = get_user()
        company = get_user_company(user)
        set_service_query(query, company)

        if req.args.get('q'):
            query['bool']['must'].append({
                'query_string': {
                    'query': req.args.get('q'),
                    'default_operator': 'AND',
                    'lenient': True,
                }
            })
            query['bool']['must_not'].append({'term': {'pubstatus': 'canceled'}})

        if req.args.get('bookmarks'):
            query['bool']['must'].append({
                'term': {'bookmarks': req.args['bookmarks']},
            })

        if req.args.get('service'):
            services = json.loads(req.args['service'])
            selected_services = [key for key in services if services[key]]
            if selected_services:
                query['bool']['must'].append({
                    'terms': {'service.code': selected_services},
                })

        source = {'query': query}
        source['sort'] = [{'versioncreated': 'desc'}]
        source['size'] = 25
        source['from'] = int(req.args.get('from', 0))
        source['post_filter'] = {'bool': {'must': []}}

        if source['from'] >= 1000:
            # https://www.elastic.co/guide/en/elasticsearch/guide/current/pagination.html#pagination
            return abort(400)

        if not source['from']:  # avoid aggregations when handling pagination
            source['aggs'] = aggregations

        if req.args.get('filter'):
            filters = json.loads(req.args['filter'])
            if filters:
                for key, val in filters.items():
                    if val:
                        query = {'terms': {get_aggregation_field(key): val}}
                        source['post_filter']['bool']['must'].append(query)

        if req.args.get('created_from') or req.args.get('created_to'):
            _range = {'time_zone': get_user_timezone()}
            if req.args.get('created_from'):
                _range['gte'] = req.args['created_from']
            if req.args.get('created_to'):
                _range['lte'] = req.args['created_to']
            source['post_filter']['bool']['must'].append(
                {'range': {'versioncreated': _range}}
            )

            print(source['post_filter'])

        internal_req = ParsedRequest()
        internal_req.args = {'source': json.dumps(source)}
        return super().get(internal_req, lookup)

    def test_new_item(self, item_id, topics, users, companies):
        query = {
            'bool': {
                'must_not': [
                    {'term': {'type': 'composite'}},
                    {'constant_score': {'filter': {'exists': {'field': 'nextversion'}}}},
                    {'term': {'pubstatus': 'canceled'}}
                ],
                'must': [
                    {'term': {'_id': item_id}}
                ],
            }
        }
        aggs = {
            'topics': {
                'filters': {
                    'filters': {}
                }
            }
        }

        queried_topics = []

        for topic in topics:
            query['bool']['must'] = [{'term': {'_id': item_id}}]

            user = users.get(str(topic['user']))
            if not user:
                continue

            topic_filter = {
                'bool': {
                    'must': [{
                        'query_string': {
                            'query': topic['query'],
                            'default_operator': 'AND',
                            'lenient': True,
                        },
                        }
                    ],
                }
            }

            company = companies.get(str(user.get('company', '')))

            # for now even if there's no active company matching for the user
            # continuing with the search
            set_service_query(topic_filter, company)

            aggs['topics']['filters']['filters'][str(topic['_id'])] = topic_filter
            queried_topics.append(topic)

        source = {'query': query}
        source['aggs'] = aggs
        source['size'] = 0

        req = ParsedRequest()
        req.args = {'source': json.dumps(source)}
        topic_matches = []

        try:
            search_results = super().get(req, None)

            for topic in queried_topics:
                if search_results.hits['aggregations']['topics']['buckets'][str(topic['_id'])]['doc_count'] > 0:
                    topic_matches.append(topic['_id'])

        except Exception as exc:
            logger.error('Error in test_new_item for query: {}'.format(json.dumps(source)),
                         exc, exc_info=True)

        return topic_matches


import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {omit, get, sortBy} from 'lodash';
import {gettext, toggleValue} from 'utils';
import {submitShareItem} from 'search/actions';
import {submitShareTopic} from 'user-profile/actions';
import {modalFormInvalid, modalFormValid} from 'actions';

import Modal from 'components/Modal';
import SearchBar from 'search/components/SearchBar';

class ShareItemModal extends React.Component<any, any> {
    static propTypes: any;
    constructor(props: any) {
        super(props);
        this.state = {
            message: '',
            users: [],
            displayUsers: this.props.data.users,
            items: this.props.data.items
        };
        this.onSubmit = this.onSubmit.bind(this);
        this.getUsers = this.getUsers.bind(this);
    }

    onSubmit(event: any) {
        event.preventDefault();
        if (this.state.users.length) {
            return this.props.submit(!!this.props.data.isTopic, omit(this.state, 'displayUsers'));
        }
    }

    onChangeHandler(field: any) {
        return (event: any) => {
            this.setState({
                [field]: event.target.value,
            });
        };
    }

    toggleUser(userId: any, all?: any) {
        let newValue: any;
        if (all) {
            newValue = this.props.data.users.length === this.state.users.length ? [] :
                this.props.data.users.map((u: any) => u._id);
        } else {
            newValue = toggleValue(this.state.users, userId);
        }

        this.setState({users: newValue});

        if (newValue.length === 0) {
            this.props.modalFormInvalid();
        } else {
            this.props.modalFormValid();
        }
    }

    toggleAllUsers() {
        this.toggleUser(null, true);
    }

    getUsers(q: any) {
        this.setState({
            displayUsers: q ? this.props.data.users.filter((u: any) =>
                (this.getUserName(u).toLowerCase()).includes(q.toLowerCase())) : this.props.data.users
        });
    }

    getUserName(user: any) {
        return `${user.first_name} ${user.last_name}`;
    }

    render() {
        const selectAllText = this.props.data.users.length === this.state.users.length ? gettext('Deselect All') :
            gettext('Select All');
        const usersList = sortBy(this.state.displayUsers, 'first_name').map((user: any, index: any) => (
            <tr key={index}>
                <td>
                    <div className="form-check form-check--flex">
                        <input id={user._id} type="checkbox"
                            className="form-check-input"
                            checked={this.state.users.indexOf(user._id) > -1}
                            onChange={() => this.toggleUser(user._id)} />
                    </div>
                </td>
                <td>
                    <div className="form-check form-check--flex">
                        <label className="form-check-label" htmlFor={user._id}>{this.getUserName(user)}</label>
                    </div>
                    
                </td>
            </tr>
        ));

        return (
            <Modal
                onSubmit={this.onSubmit}
                title={gettext('Share Item')}
                onSubmitLabel={gettext('Share')}
                disableButtonOnSubmit >

                <div className='modal-body__inner'>
                    <div className="modal-body__inner-header">
                        <SearchBar
                            fetchItems={this.getUsers}
                            enableQueryAction={false}
                        />
                    </div>
                    <form className="modal-body__inner-content inner-content-grid" onSubmit={this.onSubmit}>
                        <div className="form-group inner-content-grid__main">
                            <table className="table table--small mt-3">
                                <colgroup>
                                    <col style={{width: '8%'}} />
                                    <col style={{width: '92%'}} />
                                </colgroup>
                                <thead>
                                    {usersList.length > 0 && <tr>
                                        <th>
                                            <div className="form-check form-check--flex">
                                                <input id="check-all" type="checkbox"
                                                    className="form-check-input"
                                                    onChange={() => this.toggleAllUsers()}
                                                    checked={this.state.users.length === this.props.data.users.length}
                                                />
                                                
                                            </div>
                                        </th>
                                        <th>
                                            <div className="form-check form-check--flex">
                                                <label className="form-check-label form-check-label--strong" htmlFor="check-all">{selectAllText}</label>
                                            </div>
                                            
                                        </th>
                                    </tr>}
                                </thead>
                                <tbody>
                                    {usersList}
                                </tbody>
                            </table>
                        </div>
                        <div className="form-group user-msg inner-content-grid__footer">
                            <label className="a11y-only" htmlFor="message">{gettext('Message')}</label>
                            <textarea className="form-control"
                                id="message"
                                placeholder={gettext('Message')}
                                value={this.state.message}
                                onChange={this.onChangeHandler('message')}
                            />
                        </div>
                    </form>
                </div>
            </Modal>
        );
    }
}

ShareItemModal.propTypes = {
    submit: PropTypes.func.isRequired,
    modalFormInvalid: PropTypes.func,
    modalFormValid: PropTypes.func,
    data: PropTypes.shape({
        items: PropTypes.arrayOf(PropTypes.string).isRequired,
        users: PropTypes.arrayOf(PropTypes.shape({
            _id: PropTypes.string.isRequired,
            first_name: PropTypes.string.isRequired,
            last_name: PropTypes.string.isRequired,
        })),
        isTopic: PropTypes.bool,
    }),
};

const mapStateToProps = (state: any) => ({formValid: get(state, 'modal.formValid')});

const mapDispatchToProps = (dispatch: any) => ({
    submit: (isFolllowedTopic: any, data: any) => isFolllowedTopic ? dispatch(submitShareTopic(data)) : dispatch(submitShareItem(data)),
    modalFormInvalid: () => dispatch(modalFormInvalid()),
    modalFormValid: () => dispatch(modalFormValid()),
});

const component: React.ComponentType<any> = connect(mapStateToProps, mapDispatchToProps)(ShareItemModal);

export default component;

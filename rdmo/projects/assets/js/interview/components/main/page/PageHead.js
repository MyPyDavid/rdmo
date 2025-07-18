import React from 'react'
import PropTypes from 'prop-types'
import classNames from 'classnames'
import { capitalize, isEmpty, isNil } from 'lodash'

import useModal from 'rdmo/core/assets/js/hooks/useModal'

import { generateSetIndex } from '../../../utils/set'

import PageHeadDeleteModal from './PageHeadDeleteModal'
import PageHeadFormModal from './PageHeadFormModal'
import PageHeadReuseModal from './PageHeadReuseModal'

import PageTabsHelp from './PageTabsHelp'

const PageHead = ({ templates, page, sets, values, disabled, currentSet,
                    activateSet, createSet, updateSet, deleteSet, copySet }) => {

  const currentSetValue = isNil(currentSet) ? null : (
    values.find((value) => (
      value.set_prefix == currentSet.set_prefix && value.set_index == currentSet.set_index
    ))
  )

  const createModal = useModal()
  const updateModal = useModal()
  const copyModal = useModal()
  const importModal = useModal()
  const deleteModal = useModal()

  // inlining the title attributes caused problems with django's translation system
  const labels = {
    copy: gettext('Copy tab'),
    add: gettext('Add tab'),
    edit: gettext('Edit tab'),
    reuse: gettext('Reuse answers'),
    remove: gettext('Remove tab')
  }

  const handleActivate = (event, set) => {
    event.preventDefault()
    if (set.set_index != currentSet.set_index) {
      activateSet(set)
    }
  }

  const handleOpenCreateModal = (event) => {
    event.preventDefault()
    createModal.open()
  }

  const handleCreate = (text, copySetValue) => {
    if (isEmpty(copySetValue)) {
      createSet({
        attribute: page.attribute,
        set_index: generateSetIndex(sets, currentSet),
        set_collection: page.is_collection,
        element: page,
        text
      })
    } else {
      // TODO: check if this code is ever executed
      copySet(currentSet, copySetValue, {
        attribute: page.attribute,
        set_index: generateSetIndex(sets, currentSet),
        set_collection: page.is_collection,
        element: page,
        text
      })
    }
    createModal.close()
  }

  const handleUpdate = (text) => {
    updateSet(currentSetValue, { text })
    updateModal.close()
  }

  const handleDelete = () => {
    deleteSet(currentSet, currentSetValue)
    deleteModal.close()
  }

  const handleCopy = (text) => {
    copySet(currentSet, currentSetValue, {
      attribute: page.attribute,
      set_index: generateSetIndex(sets, currentSet),
      set_collection: page.is_collection,
      element: page,
      text
    })
    copyModal.close()
  }

  const handleImport = (copySetValue) => {
    copySet(currentSet, copySetValue, currentSetValue)
    importModal.close()
  }

  return page.is_collection && (
    <div className="interview-page-tabs">
      <PageTabsHelp templates={templates} page={page} disabled={disabled} />
      {
        currentSet ? (
          <>
            <ul className="nav nav-tabs">
              {
                sets.map((set, setIndex) => {
                  const setValue = values.find((value) => (
                    value.set_prefix == set.set_prefix && value.set_index == set.set_index
                  ))
                  return (
                    <li key={setIndex} className={classNames({active: set.set_index == currentSet.set_index})}>
                      <a href="#" onClick={(event) => handleActivate(event, set)}>
                        {isNil(setValue) ? `#${set.set_index + 1}` : setValue.text}
                      </a>
                    </li>
                  )
                })
              }
              {
                !disabled && (
                  <li>
                    <a href="" title={labels.add} className="add-set" onClick={handleOpenCreateModal}>
                      <i className="fa fa-plus fa-btn" aria-hidden="true"></i> {capitalize(page.verbose_name)}
                    </a>
                  </li>
                )
              }
            </ul>
            {
              !disabled && (
                <div className="interview-page-tabs-buttons">
                  {
                    page.attribute && (
                      <button role="button" className="btn-link fa fa-pencil"
                              title={labels.edit} onClick={updateModal.open} />
                    )
                  }
                  <button role="button" className="btn-link fa fa-copy"
                          title={labels.copy} aria-label={labels.copy}
                          onClick={copyModal.open} />
                  <button role="button" className="btn-link fa fa-arrow-circle-down"
                          title={labels.reuse} aria-label={labels.reuse}
                          onClick={importModal.open} />
                  <button role="button" className="btn-link fa fa-trash"
                          title={labels.remove} aria-label={labels.remove}
                          onClick={deleteModal.open} />
                </div>
              )
            }
          </>
        ) : (
          !disabled && (
            <button role="button" className="btn btn-success" title={labels.add} onClick={createModal.open}>
              <i className="fa fa-plus fa-btn" aria-hidden="true"></i> {capitalize(page.verbose_name)}
            </button>
          )
        )
      }

      {
        !disabled && <>
        <PageHeadFormModal
          title={gettext('Create tab')}
          submitLabel={gettext('Create')}
          submitColor="success"
          show={createModal.show}
          attribute={page.attribute}
          reuse={true}
          onClose={createModal.close}
          onSubmit={handleCreate}
        />
        <PageHeadFormModal
          title={gettext('Copy tab')}
          submitLabel={gettext('Copy')}
          submitColor="info"
          show={copyModal.show}
          attribute={page.attribute}
          onClose={copyModal.close}
          onSubmit={handleCopy}
        />
        {
          currentSetValue && (
            <PageHeadFormModal
              title={gettext('Update tab')}
              submitLabel={gettext('Update')}
              submitColor="primary"
              show={updateModal.show}
              attribute={page.attribute}
              initial={currentSetValue.text}
              onClose={updateModal.close}
              onSubmit={handleUpdate}
            />
          )
        }
        {
          currentSetValue && (
            <PageHeadReuseModal
              show={importModal.show}
              attribute={page.attribute}
              onClose={importModal.close}
              onSubmit={handleImport}
            />
          )
        }
        <PageHeadDeleteModal
          name={currentSetValue ? currentSetValue.text : null}
          show={deleteModal.show}
          onClose={deleteModal.close}
          onSubmit={handleDelete}
        />
      </>
    }
    </div>
  )
}

PageHead.propTypes = {
  templates: PropTypes.object.isRequired,
  page: PropTypes.object.isRequired,
  sets: PropTypes.array.isRequired,
  values: PropTypes.array.isRequired,
  disabled: PropTypes.bool.isRequired,
  currentSet: PropTypes.object,
  activateSet: PropTypes.func.isRequired,
  createSet: PropTypes.func.isRequired,
  updateSet: PropTypes.func.isRequired,
  deleteSet: PropTypes.func.isRequired,
  copySet: PropTypes.func.isRequired
}

export default PageHead

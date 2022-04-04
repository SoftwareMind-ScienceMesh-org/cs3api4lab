import { ReactWidget } from '@jupyterlab/apputils';
import { PanelLayout, Widget } from '@lumino/widgets';
import * as React from 'react';
import { folderIcon } from '@jupyterlab/ui-components';
import { acceptIcon, declineIcon } from './icons';
import { PendingSharesOptions } from './types';
import { Message } from '@lumino/messaging';
import { requestAPI } from './services';

export class Cs3PendingSharesWidget extends Widget {
  layout: PanelLayout;

  constructor(options: PendingSharesOptions) {
    super();
    this.id = options.id;
    this.title.label = options.title.label;
    this.title.caption = options.title.caption;
    this.title.closable = false;

    this.layout = new PanelLayout();
    this.layout.addWidget(new PendingSharesHeader(options));
    this.layout.addWidget(new PendingSharesList());
  }

  protected onResize(msg: Widget.ResizeMessage): void {
    const { width } =
      msg.width === -1 ? this.node.getBoundingClientRect() : msg;

    this.toggleClass('jp-pending-shares-narrow', width < 290);
  }
}

class PendingSharesList extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-pending-shares-listing-wrapper');
  }

  protected async onBeforeAttach(msg: Message) {
    super.onBeforeAttach(msg);
    const pendingRequest = await requestAPI(
      '/api/cs3/shares/received?status=pending',
      {
        method: 'GET'
      }
    );
    console.log('pending shares', pendingRequest);
  }

  protected render(): JSX.Element {
    const randomList: number[] = Array.from({ length: 40 }, () =>
      Math.floor(Math.random() * 40)
    );
    console.log(randomList);

    return (
      <>
        <div className="jp-pending-shares-header">
          <div className="jp-pending-shares-header-item jp-pending-shares-header-item-name">
            <span>Name</span>
          </div>
          <div className="jp-pending-shares-narrow-column">...</div>
          <div className="jp-pending-shares-header-item jp-pending-shares-header-item-shared-by jp-pending-shares-header-item-shared-by-hidden">
            <span>Shared By</span>
          </div>
          <div className="jp-pending-shares-header-item-buttons" />
        </div>
        <ul className="jp-pending-shares-listing">
          {randomList.map(() => {
            return <PendingSharesElement />;
          })}
        </ul>
      </>
    );
  }
}

class PendingSharesHeader extends ReactWidget {
  constructor(options: any) {
    super();
    this.addClass('jp-pending-shares-content');
    this.title.label = options.title.label;
  }
  protected render(): JSX.Element {
    return (
      <>
        <div className="jp-pending-shares-title c3-title-widget">
          {this.title.label}
        </div>
      </>
    );
  }
}

const PendingSharesElement = (): JSX.Element => {
  const Icon = folderIcon;
  return (
    <li
      className="jp-pending-shares-listing-item"
      title="Name: testDir
                                          Path: cs3driveShareByMe:reva/einstein
                                          Created: 2022-02-13 12:40:37
                                          Modified: 2022-02-13 12:40:37
                                          Writable: true"
    >
      <Icon.react className="jp-pending-shares-listing-icon" />
      <span className="jp-pending-shares-listing-name">
        <span>testDir</span>
      </span>
      <div className="jp-pending-shares-listing-narrow-column" />
      <span className="jp-pending-shares-listing-shared-by jp-pending-shares-listing-shared-by-hidden">
        {' '}
        John Doe
      </span>
      <div className="jp-pending-shares-listing-buttons">
        <AcceptButton />
        <RejectButton />
      </div>
    </li>
  );
};

const AcceptButton = (): JSX.Element => {
  const Icon = acceptIcon;
  return (
    <button
      className="jp-button jp-pending-shares-listing-button"
      onClick={() => {
        console.log('accept');
      }}
    >
      <Icon.react
        className="jp-pending-shares-listing-icon jp-pending-shares-listing-accept"
        width="16px"
        height="16px"
      />
    </button>
  );
};

const RejectButton = (): JSX.Element => {
  const Icon = declineIcon;
  return (
    <button
      className="jp-button jp-pending-shares-listing-button"
      onClick={() => {
        console.log('reject');
      }}
    >
      <Icon.react
        className="jp-pending-shares-listing-icon jp-pending-shares-listing-reject"
        width="16px"
        height="16px"
      />
    </button>
  );
};

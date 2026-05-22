/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface World {
  id: string;
  name: string;
  status: 'synced' | 'syncing' | 'idle' | 'error';
  lastBackup: string;
  size: string;
}

export interface User {
  name: string;
  email: string;
  avatar: string;
}

export type Theme = 'day' | 'night';
